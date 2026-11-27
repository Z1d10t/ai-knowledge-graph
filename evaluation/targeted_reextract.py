"""Stage C: targeted re-extraction of professional knowledge the v2 run did not capture.

Only the passages that matter are re-extracted: for every paper in the fixed reference set
this script collects (a) the reference scope lines and (b) the lines that mention a concept
the Stage A review marked ``confirmed_missing``, merges them into passages and sends each
passage once through the v3 term-first prompt.

The output is written to ``evaluation/targeted_reextract_v3/<paper>.json`` and fused into the
v3 layers by :mod:`evaluation.normalize_v3` (``source=targeted_reextract``). Nothing is
overwritten: an existing output is reused unless ``--force`` is given.

Usage::

    python evaluation/targeted_reextract.py --dry-run
    python evaluation/targeted_reextract.py
    python evaluation/targeted_reextract.py --papers 011,201 --force
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from knowledge_graph.config import load_config  # noqa: E402
from knowledge_graph.llm import LLMClient, extract_json_from_text  # noqa: E402
from knowledge_graph.prompts import prompt_factory  # noqa: E402
from knowledge_graph.terminology import clean_text  # noqa: E402

MD = ROOT.parent / "材料论文" / "全部_285篇" / "md"
STAGE_A = ROOT / "evaluation" / "terminology_review_20261125" / "stage_a"
OUT = ROOT / "evaluation" / "targeted_reextract_v3"
CONFIG = ROOT / "config-deepseek.toml"
MAX_PASSAGE_CHARS = 4200
CONTEXT_LINES = 1
MAX_PASSAGES = 6


def passages_for_paper(paper: str, term_records: list[dict], relation_records: list[dict],
                       scope_lines: list[int]) -> list[dict]:
    """Merge the interesting line ranges into prioritised passages."""
    md_path = next(MD.glob(paper + "*"))
    lines = md_path.read_text(encoding="utf-8").splitlines()

    priority: dict[int, int] = {}
    for number in range(scope_lines[0], scope_lines[1] + 1):
        priority[number] = 0
    needles = []
    for record in term_records:
        if record.get("verdict") == "confirmed_missing":
            needles.append(record["canonical"])
            needles.extend(record.get("aliases") or [])
    for index, line in enumerate(lines, start=1):
        lowered = clean_text(line).lower()
        if any(needle and needle.lower() in lowered for needle in needles):
            priority[index] = min(priority.get(index, 9), 1)
    for record in relation_records:
        if record.get("verdict") == "not_found":
            number = int(record["source_line"])
            priority.setdefault(number, 2)

    # contiguous ranges (gap <= 3 lines), priority = best member
    ranges: list[list[int]] = []
    for number in sorted(priority):
        if ranges and number <= ranges[-1][1] + 3:
            ranges[-1][1] = number
            ranges[-1][2] = min(ranges[-1][2], priority[number])
        else:
            ranges.append([number, number, priority[number]])

    candidates = []
    for start, end, prio in ranges:
        start = max(1, start - CONTEXT_LINES)
        end = min(len(lines), end + CONTEXT_LINES)
        text = "\n".join(line for line in lines[start - 1:end] if line.strip())
        if len(text) < 150:
            continue
        candidates.append({"lines": [start, end], "text": text, "priority": prio})

    candidates.sort(key=lambda item: (item["priority"], -len(item["text"])))
    chosen = candidates[:MAX_PASSAGES]
    chosen.sort(key=lambda item: item["lines"][0])
    return chosen


def extract_passage(client, system_prompt: str, user_template: str, passage: dict) -> dict:
    prompt = user_template + f"```\n{passage['text']}\n```\n"
    reply = client.complete(prompt, system_prompt)
    parsed = extract_json_from_text(reply, expect="object")
    if not isinstance(parsed, dict):
        return {"error": "no JSON object", "terms": [], "triples": []}
    terms = [item for item in parsed.get("terms") or [] if isinstance(item, dict) and item.get("name")]
    relations = []
    haystack = clean_text(passage["text"]).lower()
    for item in parsed.get("relations") or []:
        if not isinstance(item, dict):
            continue
        subject = str(item.get("subject") or "").strip()
        obj = str(item.get("object") or "").strip()
        predicate = str(item.get("predicate") or "").strip()
        evidence = str(item.get("evidence") or "").strip()
        if not subject or not obj or not predicate or subject == obj:
            continue
        match = bool(evidence) and clean_text(evidence)[:80].lower() in haystack
        relations.append({
            "subject": subject,
            "subject_type": str(item.get("subject_type") or "").strip().lower(),
            "predicate": predicate,
            "object": obj,
            "object_type": str(item.get("object_type") or "").strip().lower(),
            "evidence": evidence[:300],
            "evidence_level": str(item.get("evidence_level") or "stated").strip().lower(),
            "evidence_text_match": match,
            "value": item.get("value"),
            "unit": item.get("unit"),
            "property": item.get("property"),
            "chunk": 0,
        })
    return {"terms": terms, "triples": relations}


def run_paper(paper: str, scope_lines: list[int], term_records: list[dict],
              relation_records: list[dict], config: dict, force: bool) -> dict:
    output_path = OUT / f"{paper}.json"
    md_path = next(MD.glob(paper + "*"))
    source_sha = hashlib.sha256(md_path.read_bytes()).hexdigest()
    if output_path.exists() and not force:
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        if payload.get("source_sha256") == source_sha:
            return {"paper": paper, "status": "cached", "relations": len(payload.get("triples", []))}

    passages = passages_for_paper(paper, term_records, relation_records, scope_lines)
    client = LLMClient.from_config(config)
    system_prompt = prompt_factory.get_prompt("main_system_materials_v3")
    user_template = prompt_factory.get_prompt("main_user_materials_v3")

    triples, terms, passage_meta, errors = [], [], [], []
    for passage in passages:
        try:
            result = extract_passage(client, system_prompt, user_template, passage)
        except Exception as error:  # API errors should not lose the other passages
            errors.append(f"{type(error).__name__}: {error}")
            continue
        terms.extend(result["terms"])
        for triple in result["triples"]:
            triple["passage_lines"] = passage["lines"]
            triples.append(triple)
        passage_meta.append({"lines": passage["lines"], "chars": len(passage["text"]),
                             "relations": len(result["triples"]), "terms": len(result["terms"])})

    # drop duplicates inside the paper (same subject/predicate/object)
    unique, seen = [], set()
    for triple in triples:
        key = (triple["subject"].lower(), triple["predicate"].lower(), triple["object"].lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(triple)

    payload = {
        "paper": paper,
        "prompt_version": "v3",
        "model": config.get("llm", {}).get("model"),
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_sha256": source_sha,
        "scope_lines": scope_lines,
        "passages": passage_meta,
        "terms": terms,
        "triples": unique,
        "errors": errors,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"paper": paper, "status": "extracted", "passages": len(passage_meta),
            "relations": len(unique), "terms": len(terms), "errors": len(errors)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Targeted re-extraction with the v3 prompt")
    parser.add_argument("--papers", default="", help="Comma-separated paper-number prefixes")
    parser.add_argument("--force", action="store_true", help="Re-extract even when output exists")
    parser.add_argument("--dry-run", action="store_true", help="Only list passages; no API calls")
    parser.add_argument("--workers", type=int, default=3, help="Parallel papers (default 3)")
    args = parser.parse_args(argv)

    reference = json.loads((ROOT / "evaluation" / "terminology_review_20261125"
                            / "reference_and_comparison.json").read_text(encoding="utf-8"))
    term_records = json.loads((STAGE_A / "adjudication_terms.json").read_text(encoding="utf-8"))
    relation_records = json.loads((STAGE_A / "adjudication_relations.json").read_text(encoding="utf-8"))
    terms_by_paper: dict[str, list[dict]] = {}
    for record in term_records:
        terms_by_paper.setdefault(record["paper"], []).append(record)
    relations_by_paper: dict[str, list[dict]] = {}
    for record in relation_records:
        relations_by_paper.setdefault(record["paper"], []).append(record)

    papers = [(item["paper"], item["scope_lines"]) for item in reference]
    if args.papers:
        prefixes = tuple(part.strip() for part in args.papers.split(",") if part.strip())
        papers = [item for item in papers if item[0].startswith(prefixes)]

    if args.dry_run:
        total = 0
        for paper, scope in papers:
            passages = passages_for_paper(paper, terms_by_paper.get(paper, []),
                                          relations_by_paper.get(paper, []), scope)
            total += len(passages)
            print(f"{paper[:55]:55s} passages={len(passages)} "
                  f"lines={[p['lines'] for p in passages]}")
        print(f"\n{len(papers)} papers, {total} passages, no API calls made")
        return 0

    config = load_config(str(CONFIG))
    if not config:
        print("could not load config-deepseek.toml")
        return 2

    results = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {
            pool.submit(run_paper, paper, scope, terms_by_paper.get(paper, []),
                        relations_by_paper.get(paper, []), config, args.force): paper
            for paper, scope in papers
        }
        for future in as_completed(futures):
            paper = futures[future]
            try:
                result = future.result()
            except Exception as error:
                result = {"paper": paper, "status": "error", "error": f"{type(error).__name__}: {error}"}
            results.append(result)
            print(json.dumps(result, ensure_ascii=False))

    summary = {
        "papers": len(results),
        "extracted": sum(1 for r in results if r.get("status") == "extracted"),
        "cached": sum(1 for r in results if r.get("status") == "cached"),
        "errors": sum(1 for r in results if r.get("status") == "error"),
        "relations": sum(r.get("relations", 0) for r in results),
        "output": str(OUT),
    }
    (OUT / "summary.json").write_text(json.dumps({"summary": summary, "papers": results},
                                                 ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
