# -*- coding: utf-8 -*-
"""Corpus-level statistics for full_v1 after the rebuild."""
import json
import os
import re
from collections import Counter

BASE = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\ai-knowledge-graph-main\evaluation\full_v1\kg_output"
ENR = os.path.join(BASE, "enriched")

triples = []
files = sorted(f for f in os.listdir(ENR) if f.endswith(".json"))
for f in files:
    triples += json.load(open(os.path.join(ENR, f), encoding="utf-8"))

types = Counter()
canon = Counter()
unmapped = Counter()
obs = 0
num = 0
ev_rows = ev_ok = 0
for t in triples:
    types[t.get("subject_type")] += 1
    types[t.get("object_type")] += 1
    p = str(t.get("predicate") or "")
    (unmapped if t.get("unmapped") else canon)[p] += 1
    if str(t.get("object", "")).startswith("obs-") or str(t.get("subject", "")).startswith("obs-"):
        obs += 1
    if t.get("value_raw") or re.search(r"\d", str(t.get("object", ""))):
        num += 1
    if "evidence_text_match" in t:
        ev_rows += 1
        ev_ok += bool(t.get("evidence_text_match"))

n = len(triples)
print(f"papers            {len(files)}")
print(f"triples           {n}")
print(f"observation edges {obs}")
print(f"numeric facts     {num} ({num/n:.1%})")
print(f"canonical preds   {len(canon)} types")
print(f"unmapped preds    {len(unmapped)} types / {sum(unmapped.values())} edges ({sum(unmapped.values())/n:.1%})")
print(f"evidence match    {ev_ok}/{ev_rows} = {ev_ok/max(1,ev_rows):.1%}")
print("types:", dict(types.most_common(10)))
print("top canonical:", canon.most_common(10))
print("top unmapped :", unmapped.most_common(10))

json.dump({"papers": len(files), "triples": n, "observation_edges": obs, "numeric": num,
           "canonical_predicate_types": len(canon), "unmapped_predicate_types": len(unmapped),
           "unmapped_edges": sum(unmapped.values()), "evidence_rows": ev_rows,
           "evidence_text_match": ev_ok, "types": dict(types),
           "top_canonical": canon.most_common(15), "top_unmapped": unmapped.most_common(15)},
          open(os.path.join(BASE, "..", "corpus_stats.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\nwritten evaluation/full_v1/corpus_stats.json")
