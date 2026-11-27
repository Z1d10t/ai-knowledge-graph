"""Build the Stage A evidence dossiers for the 96 reference terms and 36 reference relations.

For every reference item this script answers, mechanically and reproducibly:

* does the term appear as a v2 endpoint label (exact, or only as a contained variant)?
* does it appear in a non-endpoint field (``property``, ``sample_id``, evidence text)?
* which chunk of the extracted text holds the paragraph, and did that chunk produce triples?
* which candidate triples could express the reference relation (either direction)?

The output is the *input* to a semantic review, not the review itself: the script never
decides a verdict. Verdicts live in ``adjudication_terms.json`` /
``adjudication_relations.json`` and are written by the reviewer.

Usage::

    python evaluation/stage_a_cases.py            # build case_files.json
    python evaluation/stage_a_cases.py 001 201    # print dossiers for these papers
"""
from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from knowledge_graph.terminology import (  # noqa: E402
    clean_text,
    compact_key,
    extract_parenthetical_aliases,
    normalize_key,
)

MD_DIR = ROOT.parent / "材料论文" / "全部_285篇" / "md"
V2 = ROOT / "evaluation" / "full_v2" / "kg_output"
OUT = ROOT / "evaluation" / "terminology_review_20261125" / "stage_a"
REFERENCE = ROOT / "evaluation" / "terminology_review_20261125" / "reference_and_comparison.json"

CHUNK_SIZE, CHUNK_OVERLAP = 450, 60


# --------------------------------------------------------------------------- #
# v2 indexes
# --------------------------------------------------------------------------- #
def load_triples(paper: str) -> list[dict]:
    path = V2 / "enriched" / f"{paper}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def raw_triples(paper: str) -> list[dict]:
    path = V2 / "raw" / f"{paper}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def endpoint_index(triples: list[dict]) -> dict[str, dict]:
    """Non-observation endpoint labels -> types and sample evidence."""
    index: dict[str, dict] = {}
    for position, triple in enumerate(triples):
        for side in ("subject", "object"):
            label = str(triple.get(side, ""))
            if not label or label.startswith("obs-"):
                continue
            entry = index.setdefault(label, {"types": set(), "evidence": [], "positions": [], "sides": set()})
            entry["types"].add(str(triple.get(side + "_type", "")))
            entry["positions"].append(position)
            entry["sides"].add(side)
            quote = str(triple.get("source") or triple.get("evidence_quote") or "")
            if quote and len(entry["evidence"]) < 2:
                entry["evidence"].append(quote[:220])
    return index


def field_index(triples: list[dict]) -> dict[str, list[str]]:
    """Non-endpoint fields where a label can hide: property names, sample ids, obs objects."""
    index: dict[str, list[str]] = collections.defaultdict(list)
    for position, triple in enumerate(triples):
        for field in ("property", "sample_id", "device_id", "object"):
            value = triple.get(field)
            if isinstance(value, str) and value and not value.startswith("obs-"):
                index[value].append(f"{field}#{position}")
    return index


# --------------------------------------------------------------------------- #
# text / chunk machinery
# --------------------------------------------------------------------------- #
def paper_text(paper: str) -> tuple[list[str], list[str]]:
    """(raw markdown lines, extracted chunks) for one paper.

    The extracted text is reproduced with the same front/back-matter stripping and chunking
    the v2 run used (``article/extract_corpus.py``, chunk_size=450, overlap=60), so a chunk
    index from the triples can be compared with the paragraph a reference term came from.
    """
    from article.extract_corpus import strip_back_matter, strip_front_matter
    from knowledge_graph.text_utils import chunk_text

    path = next(MD_DIR.glob(paper + "*"))
    lines = path.read_text(encoding="utf-8").splitlines()
    text = "\n".join(lines)
    text, _ = strip_front_matter(text)
    text, _ = strip_back_matter(text)
    return lines, chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)


def line_chunks(lines: list[str], chunks: list[str], start: int, end: int) -> dict[str, list[int]]:
    """Map reference scope lines to the chunk indices that contain them (1-based, as triples)."""
    mapping: dict[str, list[int]] = {}
    for number in range(start, min(end, len(lines)) + 1):
        snippet = re.sub(r"\s+", " ", lines[number - 1]).strip()
        if len(snippet) < 20:
            continue
        snippet = snippet[:60]
        hits = [i + 1 for i, chunk in enumerate(chunks) if snippet and snippet in chunk]
        mapping[str(number)] = hits
    return mapping


def chunk_coverage(triples: list[dict]) -> dict[int, int]:
    counts: dict[int, int] = collections.Counter()
    for triple in triples:
        counts[int(triple.get("chunk") or 0)] += 1
    return dict(counts)


# --------------------------------------------------------------------------- #
# matching helpers
# --------------------------------------------------------------------------- #
def term_keys(term: dict) -> list[str]:
    names = [term["canonical"]] + list(term.get("aliases") or [])
    return [normalize_key(name) for name in names if normalize_key(name)]


def label_hits(labels: list[str], keys: list[str], tokens: list[str] | None = None
               ) -> tuple[list[str], list[str], list[str]]:
    """(exact normalized matches, containment candidates, short-token matches)."""
    exact, near, token_hits = [], [], []
    for label in labels:
        key = normalize_key(label)
        if not key:
            continue
        if key in keys:
            exact.append(label)
            continue
        if any(len(k) >= 5 and (k in key or key in k) for k in keys):
            near.append(label)
            continue
        for token in tokens or []:
            if re.search(rf"(?<![A-Za-z0-9]){re.escape(token)}(?![A-Za-z0-9])", label):
                token_hits.append(label)
                break
    return exact, near, token_hits


def find_terms_in_text(lines: list[str], term: dict, start: int, end: int) -> list[dict]:
    """Where the scope lines mention the term or one of its aliases.

    Matching runs on markup-free text so ``Ga<sub>2</sub>O<sub>3</sub>`` is found for
    ``Ga2O3``.
    """
    names = [term["canonical"]] + list(term.get("aliases") or [])
    names = [n for n in names if len(n) >= 3]
    found = []
    for number in range(start, min(end, len(lines)) + 1):
        low = clean_text(lines[number - 1]).lower()
        for name in names:
            needle = clean_text(name).lower()
            if needle and needle in low:
                found.append({"line": number, "form": name})
                break
    return found


_STOP = frozenset({"the", "a", "an", "of", "in", "on", "at", "to", "for", "and", "or", "by",
                   "with", "from", "as", "is", "are", "that", "this", "these", "their"})


def _content_tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9][a-z0-9\-]+", clean_text(text).lower())
    return {w for w in words if len(w) >= 4 and w not in _STOP}


def relation_candidates(triples: list[dict], reference_keys: dict) -> list[dict]:
    """Triples that could express the reference relation, either direction.

    ``reference_keys`` carries the normalised subject/object keys *including the reference
    term's aliases*, so ``4-chlorobenzenesulfonate`` can match the v2 label ``4Cl-BZS``.
    When no label-level pair exists, a looser content-word match is tried and marked so the
    reviewer can tell the two apart.
    """
    subj_keys = reference_keys["subject"]
    obj_keys = reference_keys["object"]
    subj_tokens = reference_keys.get("subject_tokens") or set()
    obj_tokens = reference_keys.get("object_tokens") or set()

    def hits(label: str, keys: set[str]) -> bool:
        key = normalize_key(label)
        if not key:
            return False
        return any(k and (k == key or (len(k) >= 5 and (k in key or key in k))) for k in keys)

    def token_hits(label: str, tokens: set[str]) -> bool:
        return bool(tokens and (_content_tokens(label) & tokens))

    out, loose = [], []
    for position, triple in enumerate(triples):
        subject, obj = str(triple.get("subject", "")), str(triple.get("object", ""))
        if hits(subject, subj_keys) and hits(obj, obj_keys):
            direction, strength = "forward", "label"
        elif hits(subject, obj_keys) and hits(obj, subj_keys):
            direction, strength = "reverse", "label"
        elif token_hits(subject, subj_tokens) and token_hits(obj, obj_tokens):
            direction, strength = "forward", "token"
        elif token_hits(obj, subj_tokens) and token_hits(subject, obj_tokens):
            direction, strength = "reverse", "token"
        else:
            continue
        entry = {
            "position": position,
            "direction": direction,
            "strength": strength,
            "subject": subject, "predicate": triple.get("predicate"), "object": obj,
            "subject_type": triple.get("subject_type"), "object_type": triple.get("object_type"),
            "evidence": str(triple.get("source") or triple.get("evidence_quote") or "")[:220],
            "chunk": triple.get("chunk"),
        }
        (out if strength == "label" else loose).append(entry)
    return (out or loose)[:6]


# --------------------------------------------------------------------------- #
# dossier assembly
# --------------------------------------------------------------------------- #
def build() -> list[dict]:
    references = json.loads(REFERENCE.read_text(encoding="utf-8"))
    dossiers = []
    for ref in references:
        paper = ref["paper"]
        start, end = ref["scope_lines"]
        lines, chunks = paper_text(paper)
        triples = load_triples(paper)
        raw = raw_triples(paper)
        endpoints = endpoint_index(triples)
        fields = field_index(triples)
        chunk_map = line_chunks(lines, chunks, start, end)
        full_map = line_chunks(lines, chunks, 1, len(lines))
        coverage = chunk_coverage(triples)
        alias_pairs = extract_parenthetical_aliases("\n".join(lines[max(0, start - 1):end]))
        expansion = {h["alias"].lower(): h["expansion"] for h in alias_pairs}

        terms = []
        for term in ref["terms"]:
            keys = term_keys(term)
            tokens = [str(a) for a in ([term["canonical"]] + list(term.get("aliases") or []))
                      if 2 <= len(str(a)) <= 4]
            exact, near, token_hits = label_hits(list(endpoints), keys, tokens)
            near = sorted(near, key=lambda l: (len(l.split()), len(l)))[:5]
            token_hits = token_hits[:2]
            field_hits = [label for label in fields
                          if any(label_hits([label], keys, tokens))]
            obs_hits = [str(t.get("object")) for t in triples
                        if str(t.get("subject", "")).startswith("obs-")
                        and any(label_hits([str(t.get("object") or "")], keys, tokens))]
            evidence_hits = [str(t.get("source") or "") for t in triples
                             if any(label_hits([str(t.get("source") or "")], keys, tokens))]
            mentions = find_terms_in_text(lines, term, start, end)
            term_chunks = sorted({c for line in mentions for c in chunk_map.get(str(line["line"]), [])})
            body_mentions = find_terms_in_text(lines, term, 1, len(lines))
            body_chunks = sorted({c for line in body_mentions for c in full_map.get(str(line["line"]), [])})
            terms.append({
                "canonical": term["canonical"],
                "category": term["category"],
                "aliases": term.get("aliases") or [],
                "v2_status": term.get("v2_status"),
                "exact_labels": [{"label": l, "types": sorted(endpoints[l]["types"])} for l in exact],
                "near_labels": [{"label": l, "types": sorted(endpoints[l]["types"]),
                                 "evidence": endpoints[l]["evidence"][:1]} for l in near],
                "token_labels": [{"label": l, "types": sorted(endpoints[l]["types"])} for l in token_hits],
                "observed_in_fields": sorted(set(field_hits))[:5],
                "observed_as_observation_objects": sorted(set(obs_hits))[:3],
                "observed_in_evidence_text": sorted(set(evidence_hits))[:2],
                "paper_aliases": [h for h in alias_pairs
                                  if compact_key(h["alias"]) in keys or compact_key(h["expansion"]) in keys],
                "source_mentions": mentions[:4],
                "source_chunks": term_chunks,
                "chunk_triple_counts": {str(c): coverage.get(c, 0) for c in term_chunks},
                "body_mentions": {"lines": len(body_mentions), "lines_in_extracted_text": sum(
                    1 for line in body_mentions if full_map.get(str(line["line"]))),
                    "sample_lines": [line["line"] for line in body_mentions[:6]],
                    "chunks": body_chunks, "chunk_triple_counts": {str(c): coverage.get(c, 0) for c in body_chunks}},
            })

        relations = []
        term_alias_map: dict[str, set[str]] = {}
        for term in ref["terms"]:
            names = {normalize_key(x) for x in [term["canonical"]] + list(term.get("aliases") or [])}
            for name in names:
                term_alias_map.setdefault(name, set()).update(names)
        for rel in ref["relations"]:
            subj_keys = {normalize_key(rel["subject"])} | term_alias_map.get(normalize_key(rel["subject"]), set())
            obj_keys = {normalize_key(rel["object"])} | term_alias_map.get(normalize_key(rel["object"]), set())
            # a relation endpoint may also be one of the paper's parenthetical expansions
            for hit in alias_pairs:
                if compact_key(hit["alias"]) in {compact_key(rel["subject"]), compact_key(rel["object"])}:
                    subj_keys.add(normalize_key(hit["expansion"]))
                    obj_keys.add(normalize_key(hit["expansion"]))
            relations.append({
                "reference": {k: rel[k] for k in ("subject", "predicate", "object", "line")},
                "evidence": rel["evidence"][:300],
                "candidates": relation_candidates(triples, {
                    "subject": subj_keys, "object": obj_keys,
                    "subject_tokens": _content_tokens(rel["subject"]),
                    "object_tokens": _content_tokens(rel["object"]),
                }),
            })

        dossiers.append({
            "paper": paper,
            "kind": ref["kind"],
            "scope_lines": [start, end],
            "line_chunks": chunk_map,
            "chunk_coverage": coverage,
            "total_triples": len(triples),
            "raw_triples": len(raw),
            "abbreviation_aliases": alias_pairs,
            "terms": terms,
            "relations": relations,
        })
    return dossiers


def print_dossier(dossier: dict, brief: bool = False) -> None:
    print(f"\n=== {dossier['paper']} ({dossier['kind']}, lines {dossier['scope_lines'][0]}-"
          f"{dossier['scope_lines'][1]}, {dossier['total_triples']} triples) ===")
    print("scope chunks:", {k: v for k, v in dossier["line_chunks"].items() if v})
    print("triples per chunk:", dossier["chunk_coverage"])
    if dossier["abbreviation_aliases"] and not brief:
        print("paper aliases:", [(a["alias"], a["expansion"]) for a in dossier["abbreviation_aliases"]][:8])
    for term in dossier["terms"]:
        exact = ", ".join(f"{e['label']}({'/'.join(e['types'])})" for e in term["exact_labels"]) or "-"
        near = ", ".join(f"{e['label']}({'/'.join(e['types'])})" for e in term["near_labels"][:3]) or "-"
        token = ", ".join(e["label"] for e in term.get("token_labels") or []) or "-"
        body = term.get("body_mentions") or {}
        if brief:
            print(f"- {term['canonical']} [{term['category']}] v2={term['v2_status']}")
            print(f"    exact: {exact}")
            print(f"    near : {near}")
            if token != "-":
                print(f"    token: {token}")
            print(f"    fields={len(term['observed_in_fields'])} obs={len(term['observed_as_observation_objects'])} "
                  f"evidence={len(term['observed_in_evidence_text'])} | body {body.get('lines_in_extracted_text')}"
                  f"/{body.get('lines')} lines in text | scope chunks {term['source_chunks']}")
        else:
            print(f"\n- TERM {term['canonical']} [{term['category']}] aliases={term['aliases']} "
                  f"v2={term['v2_status']}")
            print(f"    exact: {term['exact_labels']}")
            print(f"    near : {term['near_labels']}")
            if term.get("token_labels"):
                print(f"    token: {term['token_labels']}")
            print(f"    fields: {term['observed_in_fields']}  obs: {term['observed_as_observation_objects']}  "
                  f"evidence: {term['observed_in_evidence_text']}")
            print(f"    source mentions: {term['source_mentions']}  chunks: {term['source_chunks']} "
                  f"triples/chunk: {term['chunk_triple_counts']}")
            print(f"    body: {body.get('lines')} mentions, {body.get('lines_in_extracted_text')} in extracted text, "
                  f"lines {body.get('sample_lines')} chunks {body.get('chunks')} triples {body.get('chunk_triple_counts')}")
    for rel in dossier["relations"]:
        ref = rel["reference"]
        print(f"- REL {ref['subject']} -> {ref['predicate']} -> {ref['object']} (L{ref['line']})")
        for cand in rel["candidates"]:
            print(f"    [{cand['position']}] {cand['subject'][:70]} -> {cand['predicate']} -> "
                  f"{cand['object'][:70]} ({cand['direction']}/{cand['strength']})")
            if not brief:
                print(f"        {cand['evidence'][:150]}")
        if not rel["candidates"]:
            print("    (no candidate triple)")


def main(argv: list[str]) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    dossiers = build()
    (OUT / "case_files.json").write_text(json.dumps(dossiers, ensure_ascii=False, indent=1), encoding="utf-8")
    brief = "--full" not in argv
    prefixes = [a for a in argv if a[:3].isdigit()]
    if prefixes:
        for dossier in dossiers:
            if any(dossier["paper"].startswith(p) for p in prefixes):
                print_dossier(dossier, brief=brief)
    else:
        counts = collections.Counter()
        for dossier in dossiers:
            for term in dossier["terms"]:
                counts[term["v2_status"]] += 1
        print("dossiers:", len(dossiers), "terms:", sum(counts.values()), dict(counts))
        print("relations:", sum(len(d["relations"]) for d in dossiers))
        print("written:", OUT / "case_files.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
