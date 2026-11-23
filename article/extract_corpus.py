#!/usr/bin/env python3
"""Batch-extract the semiconductor corpus with DeepSeek's official API.

The archive contains two copies of the same 100 papers:
  semiconductor_md/    -> 100 Markdown files (used)
  semiconductor_pdfs/  -> 100 PDFs (ignored; same stems, would duplicate work)

Pipeline per paper:
  1. Phase 1 extraction through the project's LLMClient (DeepSeek API).
  2. Rule-based standardization + taxonomy inference (no extra API calls by default).
  3. Optional HTML rendering (no LLM; community naming disabled).

Source selection:
  --source md (default) uses Markdown only; semiconductor_pdfs/ is ignored.
  --source auto (opt-in) adds a PDF fallback when the MD/PDF word ratio is below
  0.80 *and* the Markdown tail stops mid-sentence (e.g. 087 and 043 in this corpus).
  --source pdf (opt-in) forces PDF. PDF modes need pypdf: pip install pypdf
  (or the project's [pdf] extra).

  References, acknowledgements, funding and author-contribution sections are cut
  before extraction (--keep-back-matter disables this).

Outputs (resumable):
  <output>/raw/<paper>.json        extracted triples
  <output>/enriched/<paper>.json   after standardization + inference
  <output>/html/<paper>.html       only with --html
  <output>/summary.json / .csv     per-paper status and counts

Usage:
  export DEEPSEEK_API_KEY=sk-...
  python article/extract_corpus.py --dry-run
  python article/extract_corpus.py --limit 1
  python article/extract_corpus.py
  python article/extract_corpus.py --html
  python article/extract_corpus.py --full-pipeline   # also LLM standardization/inference
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import logging
import os
import re
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from knowledge_graph.config import load_config  # noqa: E402
from knowledge_graph.entity_standardization import infer_relationships, standardize_entities  # noqa: E402
from knowledge_graph.logging_utils import configure_logging  # noqa: E402
from knowledge_graph.main import InputError, process_documents, read_input_text  # noqa: E402
from knowledge_graph.visualization import build_graph_data, render_knowledge_graph  # noqa: E402

ARCHIVE = ROOT / "article" / "extracted" / "半导体论文"
DEFAULT_INPUT = ARCHIVE / "semiconductor_md"
DEFAULT_PDF_DIR = ARCHIVE / "semiconductor_pdfs"
DEFAULT_OUTPUT = ARCHIVE / "kg_output"
DEFAULT_CONFIG = ROOT / "config-deepseek.toml"

SUMMARY_FIELDS = ["id", "title", "status", "source", "md_words", "pdf_words", "md_pdf_ratio", "source_reason",
                  "stripped_back_matter", "removed_chars", "text_chars", "strip_reason",
                  "raw_triples", "enriched_triples", "inferred", "communities", "elapsed_sec", "error",
                  "raw_path", "enriched_path", "html_path"]


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Batch-extract every Markdown paper with the DeepSeek official API")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="TOML config (default: config-deepseek.toml)")
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT), help="Directory containing the .md papers")
    parser.add_argument("--pdf-dir", default=str(DEFAULT_PDF_DIR),
                        help="PDF directory; only used to verify that it mirrors the Markdown set")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT), help="Where raw/enriched/summary files go")
    parser.add_argument("--pattern", default="*.md", help="Glob under --input-dir (default: *.md)")
    parser.add_argument("--source", choices=("auto", "md", "pdf"), default="md",
                        help="Text source (default: md; auto adds a PDF fallback; pdf forces PDF)")
    parser.add_argument("--min-md-ratio", type=float, default=0.80,
                        help="auto mode: fall back to PDF when md/pdf word ratio is below this (default 0.80)")
    parser.add_argument("--start", type=int, default=1, help="1-based index of the first paper to process")
    parser.add_argument("--limit", type=int, default=0, help="Process at most N papers (0 = all)")
    parser.add_argument("--force", action="store_true", help="Re-extract even when outputs exist")
    parser.add_argument("--re-enrich", action="store_true",
                        help="Re-run standardization/inference from existing raw JSON (no extraction calls)")
    parser.add_argument("--html", action="store_true", help="Render one self-contained HTML page per paper")
    parser.add_argument("--dry-run", action="store_true", help="List papers and config, then exit without API calls")
    parser.add_argument("--fail-fast", action="store_true", help="Stop at the first failed paper")
    parser.add_argument("--continue-on-error", action="store_true",
                        help="Skip failed chunks inside a paper instead of failing the whole paper")
    parser.add_argument("--retries", type=int, default=2, help="Paper-level retries after an API/parse failure")
    parser.add_argument("--full-pipeline", action="store_true",
                        help="Enable the project's LLM entity-resolution and LLM inference passes too")
    parser.add_argument("--llm-standardization", action="store_true", help="Enable only the LLM entity-resolution pass")
    parser.add_argument("--llm-inference", action="store_true", help="Enable only the LLM bridge/hub/within passes")
    parser.add_argument("--keep-back-matter", action="store_true",
                        help="Keep references/acknowledgements/author contributions (default: strip them)")
    parser.add_argument("--no-taxonomy", action="store_true", help="Disable the deterministic taxonomy rule")
    parser.add_argument("--transitive", action="store_true", help="Enable transitive rule inference")
    parser.add_argument("--verbose", action="store_true", help="Show the pipeline's INFO logs")
    parser.add_argument("--quiet", action="store_true", help="Only show errors")
    return parser.parse_args(argv)


def rel(path) -> str:
    path = Path(path)
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def load_json(path: Path) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def paper_title(path: Path) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.startswith("# "):
                    return line[2:].strip()
    except OSError:
        pass
    return ""


_REFERENCE_HEADING = re.compile(r"(?im)^\s*(?:#+\s*)?\**\s*references\s*\**\s*:?\s*$")
_REFERENCE_WORD = re.compile(r"(?i)\b(?:references?(?:\s+and\s+notes)?|bibliography|notes\s+and\s+references)\b")
_REFERENCE_LINE = re.compile(r"(?m)^\s*(?:\[?\d+[\].)]|\(\d+\)|\d+\.)\s+\S")
_BACK_MATTER_WORD = re.compile(
    r"(?i)\b(?:acknowledg(?:e)?ments?|author\s+contributions?|funding|competing\s+interests?|"
    r"data\s+and\s+materials\s+availability|supplementary\s+materials?)\b")


def _heading_like(text: str, match: re.Match) -> bool:
    """Reject prose mentions ("references which employ...") and accept real section headings."""
    line_start = text.rfind("\n", 0, match.start()) + 1
    prefix = text[line_start:match.start()]
    after = text[match.end():match.end() + 60].lstrip()
    if after[:1].islower():
        return False
    cleaned = re.sub(r"[#*_\s\d.:\-]+", "", prefix).lower()
    if len(cleaned) > 20 and "submittedmanuscript" not in cleaned and "confidential" not in cleaned:
        return False
    return True


def strip_back_matter(text: str) -> tuple[str, dict]:
    """Drop the bibliography and end-matter before extraction.

    Reference lists produce hundreds of low-value triples ("paper X published in Y"),
    and author-contribution/funding sections produce "performed", "funded" noise.
    The header metadata table is kept; only the tail is cut.
    """
    cut = None
    # The last heading-like "references" followed by several numbered entries is the bibliography.
    for match in reversed(list(_REFERENCE_WORD.finditer(text))):
        if len(text) - match.start() < 500 or not _heading_like(text, match):
            continue
        tail = text[match.start():]
        if len(_REFERENCE_LINE.findall(tail)) >= 3:
            cut = match.start()
            break
    # End-matter headings after the main text are also dropped.
    for match in _BACK_MATTER_WORD.finditer(text):
        if (match.start() > len(text) * 0.6 and _heading_like(text, match)
                and (cut is None or match.start() < cut)):
            cut = match.start()
    if cut is None or cut < len(text) * 0.3:
        return text, {"stripped_back_matter": False, "removed_chars": 0, "text_chars": len(text)}
    stripped = text[:cut].rstrip()
    return stripped, {"stripped_back_matter": True, "removed_chars": len(text) - len(stripped),
                     "text_chars": len(stripped),
                     "strip_reason": text[cut:cut + 80].replace("\n", " ")}


def _tail_lines(text: str) -> list[str]:
    """Non-empty lines with page numbers and publisher boilerplate removed from the end."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    while lines and (re.fullmatch(r"\d+", lines[-1])
                     or lines[-1].startswith(("©", "https://doi.org", "http://dx.doi.org"))
                     or "creative commons" in lines[-1].lower()):
        lines.pop()
    return lines


def md_looks_truncated(text: str) -> bool:
    """True when the Markdown body stops mid-sentence instead of at a conclusion/reference/caption."""
    lines = _tail_lines(text)
    if not lines:
        return True
    last = lines[-1]
    if last.endswith((".", "!", "?", ";", ":", ")", "]", "}", '"', "'", "。", "！", "？")):
        return False
    # A cut inside the reference list does not matter for extraction; the body is complete.
    heading = _REFERENCE_HEADING.search(text)
    if heading and len([line for line in text[heading.end():].splitlines() if line.strip()]) >= 5:
        return False
    return True


def choose_source(md_path: Path, pdf_dir: Path, args):
    """Pick Markdown or PDF for one paper; returns (path, text, provenance info)."""
    md_text = read_input_text(md_path)
    md_words = len(md_text.split())
    pdf_path = Path(pdf_dir) / f"{md_path.stem}.pdf"
    if args.source == "md" or not pdf_path.exists():
        reason = "forced md" if args.source == "md" else "pdf missing"
        return md_path, md_text, {"source": "md", "md_words": md_words, "pdf_words": "",
                                  "md_pdf_ratio": "", "source_reason": reason}
    try:
        pdf_text = read_input_text(pdf_path)
        pdf_words = len(pdf_text.split())
    except InputError as e:
        return md_path, md_text, {"source": "md", "md_words": md_words, "pdf_words": "",
                                  "md_pdf_ratio": "", "source_reason": f"pdf unavailable: {e}"}
    ratio = md_words / max(pdf_words, 1)
    info = {"md_words": md_words, "pdf_words": pdf_words, "md_pdf_ratio": round(ratio, 3)}
    if args.source == "pdf":
        return pdf_path, pdf_text, {"source": "pdf", **info, "source_reason": "forced pdf"}
    if ratio < args.min_md_ratio and md_looks_truncated(md_text):
        return pdf_path, pdf_text, {"source": "pdf", **info,
                                    "source_reason": f"md/pdf={ratio:.2f} and md tail looks truncated"}
    return md_path, md_text, {"source": "md", **info, "source_reason": f"md/pdf={ratio:.2f}"}


def load_summary(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    if isinstance(data, dict):
        return data
    return {row["id"]: row for row in data if isinstance(row, dict) and "id" in row}


def write_summary(summary_path: Path, rows: list) -> None:
    write_json(summary_path, rows)
    csv_path = summary_path.with_suffix(".csv")
    tmp = csv_path.with_suffix(csv_path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in SUMMARY_FIELDS})
    os.replace(tmp, csv_path)


def extract_raw(doc_path: Path, text: str, config: dict, args) -> list:
    """Phase 1 only: chunk the paper and call the LLM for every chunk."""
    phase1 = copy.deepcopy(config)
    phase1.setdefault("standardization", {})["enabled"] = False
    phase1.setdefault("inference", {})["enabled"] = False
    phase1.setdefault("visualization", {})["name_communities"] = False

    last_error = None
    for attempt in range(1, max(1, args.retries) + 1):
        try:
            raw = process_documents(phase1, [(doc_path.name, text)],
                                    continue_on_error=args.continue_on_error)
            if raw:
                return raw
            last_error = "no triples extracted"
        except Exception as e:  # API errors, truncation, JSON failures, ...
            last_error = f"{type(e).__name__}: {e}"
        if attempt < max(1, args.retries):
            delay = min(30, 5 * attempt)
            print(f"    retry {attempt}/{args.retries} in {delay}s ({last_error})", flush=True)
            time.sleep(delay)
    raise RuntimeError(last_error or "extraction failed")


def enrich(raw: list, config: dict, args) -> list:
    """Phases 2-3: rule-based by default, LLM passes only when requested."""
    cfg = copy.deepcopy(config)
    std = cfg.setdefault("standardization", {})
    inf = cfg.setdefault("inference", {})
    std["use_llm_for_entities"] = bool(args.full_pipeline or args.llm_standardization)
    inf["use_llm_for_inference"] = bool(args.full_pipeline or args.llm_inference)
    inf["taxonomy"] = not args.no_taxonomy
    inf["apply_transitive"] = bool(args.transitive)
    inf["lexical"] = False

    triples = standardize_entities(raw, cfg) if std.get("enabled", True) else raw
    triples = infer_relationships(triples, cfg) if inf.get("enabled", True) else triples
    return triples


def render_page(triples: list, html_path: Path, config: dict) -> dict:
    cfg = copy.deepcopy(config)
    cfg.setdefault("visualization", {})["name_communities"] = False
    stats, _ = render_knowledge_graph(triples, str(html_path), config=cfg)
    return stats


def main(argv=None) -> int:
    args = parse_args(argv)
    level = logging.ERROR if args.quiet else (logging.INFO if args.verbose else logging.WARNING)
    configure_logging(level)

    # A dry run should work before the key is configured: resolve the env: reference
    # with a throwaway value, then restore the environment.
    placeholder = False
    if args.dry_run and not os.environ.get("DEEPSEEK_API_KEY"):
        os.environ["DEEPSEEK_API_KEY"] = "dry-run"
        placeholder = True
    config = load_config(args.config)
    if placeholder:
        os.environ.pop("DEEPSEEK_API_KEY", None)
    if not config:
        print(f"Could not load {args.config}.\n"
              "Set your key first, for example:\n"
              "  export DEEPSEEK_API_KEY=sk-...\n"
              "or replace the api_key line in config-deepseek.toml.", flush=True)
        return 2

    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        print(f"Input directory not found: {input_dir}", flush=True)
        return 2
    all_md = sorted(input_dir.glob(args.pattern))
    if not all_md:
        print(f"No files matching {args.pattern!r} in {input_dir}", flush=True)
        return 2

    pdf_dir = Path(args.pdf_dir)
    pdf_stems = {p.stem for p in pdf_dir.glob("*.pdf")} if pdf_dir.is_dir() else set()
    md_stems = {p.stem for p in all_md}
    print(f"Markdown papers : {len(all_md)}")
    pdf_usage = "ignored (--source md)" if args.source == "md" else "available for --source auto/pdf"
    if pdf_stems:
        if pdf_stems == md_stems:
            print(f"PDF folder      : {len(pdf_stems)} PDFs, identical stems; {pdf_usage}")
        else:
            md_only = sorted(md_stems - pdf_stems)
            pdf_only = sorted(pdf_stems - md_stems)
            print(f"PDF folder      : {len(pdf_stems)} PDFs, stems differ "
                  f"(md-only={len(md_only)}, pdf-only={len(pdf_only)}); Markdown is used")
            if md_only[:3] or pdf_only[:3]:
                print(f"                  md-only sample={md_only[:3]} pdf-only sample={pdf_only[:3]}")
    print(f"Model           : {config['llm']['model']}")
    print(f"Endpoint        : {config['llm']['base_url']}")
    print(f"Chunking        : {config['chunking']['chunk_size']} words / {config['chunking']['overlap']} overlap")
    source_note = {"md": " (Markdown only; PDF is never read)", "pdf": " (forced PDF)",
                   "auto": f" (PDF only when md/pdf < {args.min_md_ratio} and the md tail is truncated)"}[args.source]
    print(f"Source          : {args.source}{source_note}")
    print(f"LLM passes      : extraction=on, standardization={config['standardization'].get('use_llm_for_entities')}, "
          f"inference={config['inference'].get('use_llm_for_inference')}")

    papers = all_md[max(0, args.start - 1):]
    if args.limit > 0:
        papers = papers[:args.limit]
    if not papers:
        print("No papers selected.", flush=True)
        return 0
    print(f"Selected        : {len(papers)} (start={args.start}, limit={args.limit or 'all'})")
    print(f"First / last    : {papers[0].name} / {papers[-1].name}")
    print(f"Output          : {rel(Path(args.output_dir))}")

    if args.dry_run:
        print("\nDry run: no API calls made.")
        return 0

    out_dir = Path(args.output_dir)
    raw_dir, enriched_dir, html_dir = out_dir / "raw", out_dir / "enriched", out_dir / "html"
    raw_dir.mkdir(parents=True, exist_ok=True)
    enriched_dir.mkdir(parents=True, exist_ok=True)
    if args.html:
        html_dir.mkdir(parents=True, exist_ok=True)

    summary_path = out_dir / "summary.json"
    summary = load_summary(summary_path)
    started_all = time.time()

    for index, md_path in enumerate(papers, start=1):
        stem = md_path.stem
        raw_path = raw_dir / f"{stem}.json"
        enriched_path = enriched_dir / f"{stem}.json"
        html_path = html_dir / f"{stem}.html"
        started = time.time()
        raw, triples, status = [], [], ""
        source_fields = ("source", "md_words", "pdf_words", "md_pdf_ratio", "source_reason",
                         "stripped_back_matter", "removed_chars", "text_chars", "strip_reason")
        source_info = {}

        try:
            if enriched_path.exists() and not args.force and not args.re_enrich:
                triples = load_json(enriched_path)
                raw = load_json(raw_path)
                status = "skipped"
                source_info = {key: summary.get(stem, {}).get(key, "") for key in source_fields}
            else:
                if raw_path.exists() and not args.force:
                    raw = load_json(raw_path)
                    status = "enriched-from-raw"
                    source_info = {key: summary.get(stem, {}).get(key, "") for key in source_fields}
                    source_info["source"] = source_info.get("source") or "raw-reused"
                    source_info["source_reason"] = source_info.get("source_reason") or "raw json reused"
                else:
                    doc_path, doc_text, source_info = choose_source(md_path, pdf_dir, args)
                    if not args.keep_back_matter:
                        doc_text, strip_info = strip_back_matter(doc_text)
                        source_info.update(strip_info)
                    raw = extract_raw(doc_path, doc_text, config, args)
                    write_json(raw_path, raw)
                    status = "extracted"
                if not raw:
                    raise RuntimeError("raw extraction is empty")
                triples = enrich(raw, config, args)
                write_json(enriched_path, triples)

            stats = build_graph_data(triples)["meta"]["stats"]
            if args.html and (args.force or args.re_enrich or not html_path.exists()):
                render_page(triples, html_path, config)

            row = {
                "id": stem,
                "title": paper_title(md_path),
                "status": status,
                **{key: source_info.get(key, "") for key in source_fields},
                "raw_triples": len(raw),
                "enriched_triples": len(triples),
                "inferred": stats["inferred_edges"],
                "communities": stats["communities"],
                "elapsed_sec": round(time.time() - started, 1),
                "error": "",
                "raw_path": rel(raw_path) if raw_path.exists() else "",
                "enriched_path": rel(enriched_path) if enriched_path.exists() else "",
                "html_path": rel(html_path) if html_path.exists() else "",
            }
            print(f"[{index}/{len(papers)}] {stem}: {status} [{source_info.get('source', '?')}], "
                  f"{len(raw)} raw -> {len(triples)} enriched, {stats['inferred_edges']} inferred, "
                  f"{row['elapsed_sec']}s", flush=True)
        except Exception as e:
            row = {
                "id": stem,
                "title": paper_title(md_path),
                "status": "error",
                **{key: source_info.get(key, "") for key in source_fields},
                "raw_triples": len(raw),
                "enriched_triples": len(triples),
                "inferred": "",
                "communities": "",
                "elapsed_sec": round(time.time() - started, 1),
                "error": f"{type(e).__name__}: {e}",
                "raw_path": rel(raw_path) if raw_path.exists() else "",
                "enriched_path": rel(enriched_path) if enriched_path.exists() else "",
                "html_path": rel(html_path) if html_path.exists() else "",
            }
            print(f"[{index}/{len(papers)}] {stem}: ERROR {row['error']}", flush=True)
            if args.verbose:
                traceback.print_exc()

        summary[stem] = row
        write_summary(summary_path, [summary[k] for k in sorted(summary)])
        if row["status"] == "error" and args.fail_fast:
            print("Stopping because of --fail-fast.", flush=True)
            break

    rows = [summary[k] for k in sorted(summary)]
    write_summary(summary_path, rows)
    ok = sum(1 for r in rows if r.get("status") != "error")
    errors = [r for r in rows if r.get("status") == "error"]
    total_triples = sum(int(r.get("enriched_triples") or 0) for r in rows)
    print(f"\nDone: {ok} ok, {len(errors)} error(s), {total_triples} enriched triples total, "
          f"{time.time() - started_all:.0f}s", flush=True)
    print(f"Summary: {rel(summary_path)}  /  {rel(summary_path.with_suffix('.csv'))}")
    if errors:
        print("Failed papers:", ", ".join(r["id"] for r in errors), flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
