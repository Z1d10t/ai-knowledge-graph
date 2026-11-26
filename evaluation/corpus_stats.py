# -*- coding: utf-8 -*-
"""Corpus-level statistics for the 30-paper evaluation run (predictions side)."""
import csv
import json
import os
import re
from collections import Counter

ROOT = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\ai-knowledge-graph-main"
EVAL = os.path.join(ROOT, "evaluation")
ENR = os.path.join(EVAL, "kg_output_eval", "enriched")

triples = []
files = sorted(f for f in os.listdir(ENR) if f.endswith(".json"))
for f in files:
    triples += json.load(open(os.path.join(ENR, f), encoding="utf-8"))

types = Counter()
preds = Counter()
unmapped = Counter()
obs = 0
num = 0
ev_rows = ev_ok = 0
for t in triples:
    types[t.get("subject_type")] += 1
    types[t.get("object_type")] += 1
    p = str(t.get("predicate") or "")
    if t.get("unmapped"):
        unmapped[p] += 1
    else:
        preds[p] += 1
    if str(t.get("object", "")).startswith("obs-") or str(t.get("subject", "")).startswith("obs-"):
        obs += 1
    if t.get("value_raw") or re.search(r"\d", str(t.get("object", ""))):
        num += 1
    if "evidence_text_match" in t:
        ev_rows += 1
        ev_ok += bool(t.get("evidence_text_match"))

rows = list(csv.DictReader(open(os.path.join(EVAL, "kg_output_eval", "summary.csv"), encoding="utf-8")))
chunks = sum(int(r.get("chunks") or 0) for r in rows)
retried = sum(int(r.get("empty_retried") or 0) for r in rows)
recovered = sum(int(r.get("empty_recovered") or 0) for r in rows)
failed = sum(int(r.get("empty_failed") or 0) for r in rows)
elapsed = sum(float(r.get("elapsed_sec") or 0) for r in rows)
canon_types = {p for p in preds}

print(f"papers                 {len(files)}")
print(f"triples                {len(triples)}")
print(f"observation edges      {obs}")
print(f"numeric facts          {num} ({num/len(triples):.1%})")
print(f"canonical predicates   {len(canon_types)} types")
print(f"unmapped predicates    {len(unmapped)} types / {sum(unmapped.values())} edges")
print(f"top unmapped           {unmapped.most_common(8)}")
print(f"evidence text match    {ev_ok}/{ev_rows} = {ev_ok/max(1,ev_rows):.1%}")
print(f"types                  {dict(types.most_common(8))}")
print(f"chunks                 {chunks} (retried {retried}, recovered {recovered}, failed {failed})")
print(f"extraction time        {elapsed:.0f}s = {elapsed/60:.1f} min")

meta = {
    "papers": len(files), "triples": len(triples), "observations": obs, "numeric": num,
    "canonical_predicate_types": len(canon_types), "unmapped_predicate_types": len(unmapped),
    "unmapped_edges": sum(unmapped.values()), "unmapped_top": unmapped.most_common(10),
    "evidence_rows": ev_rows, "evidence_text_match": ev_ok,
    "types": dict(types), "chunks": chunks, "empty_retried": retried,
    "empty_recovered": recovered, "empty_failed": failed, "elapsed_sec": elapsed,
}
json.dump(meta, open(os.path.join(EVAL, "corpus_stats.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nwritten evaluation/corpus_stats.json")
