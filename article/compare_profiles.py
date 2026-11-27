# -*- coding: utf-8 -*-
"""Compare the generic baseline run with the materials-profile run."""
import json
import os
import re
import collections

BASE = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\ai-knowledge-graph-main\article\extracted\semiconductor_pilot"
JUNK = {"of", "in", "at", "between", "for", "by", "with", "on", "to", "from", "is", "has", "have"}
GENERIC_TYPES = {"person", "organization", "place", "event", "technology", "product", "work", "date", "concept"}
MATERIAL_TYPES = {"material", "material_class", "sample", "structure", "device", "process", "condition",
                  "property", "measurement", "characterization", "mechanism", "defect", "interface"}


def load(folder):
    d = os.path.join(BASE, folder, "enriched")
    out = []
    for f in sorted(os.listdir(d)):
        out += json.load(open(os.path.join(d, f), encoding="utf-8"))
    return out


def stats(triples, label):
    types = collections.Counter()
    preds = collections.Counter()
    numeric = 0
    verified = 0
    obs = 0
    unmapped = 0
    for t in triples:
        types[t.get("subject_type")] += 1
        types[t.get("object_type")] += 1
        preds[t.get("predicate")] += 1
        if t.get("unmapped"):
            unmapped += 1
        if t.get("value_raw") or re.search(r"\d", str(t.get("object", ""))):
            numeric += 1
        if t.get("evidence_verified"):
            verified += 1
        if str(t.get("object", "")).startswith("obs-") or str(t.get("subject", "")).startswith("obs-"):
            obs += 1
    n = max(1, len(triples))
    junk = sum(v for k, v in preds.items() if k in JUNK)
    generic = sum(v for k, v in types.items() if k in GENERIC_TYPES)
    material = sum(v for k, v in types.items() if k in MATERIAL_TYPES)
    print(f"\n=== {label} ===")
    print(f"triples            {len(triples)}")
    print(f"unique predicates  {len(preds)}")
    print(f"junk predicates    {junk} ({junk/n:.1%})")
    print(f"generic types      {generic} ({generic/(2*n):.1%})")
    print(f"materials types    {material} ({material/(2*n):.1%})")
    print(f"numeric facts      {numeric} ({numeric/n:.1%})")
    print(f"observation nodes  {obs}")
    print(f"evidence verified  {verified} ({verified/n:.1%})")
    print(f"unmapped predicates {unmapped}")
    print("top predicates:", ", ".join(f"{k}:{v}" for k, v in preds.most_common(10)))
    print("types:", ", ".join(f"{k or 'None'}:{v}" for k, v in types.most_common(8)))
    return preds


base = load("kg_output")
new = load("kg_output_materials")
stats(base, "generic baseline (kg_output)")
stats(new, "materials profile (kg_output_materials)")

print("\n--- 12 materials-profile triples ---")
shown = 0
for t in new:
    if t.get("value_raw") or t.get("predicate") in ("is a", "passivated by", "has efficiency"):
        print(f"  {t.get('subject','')[:44]:44} | {t.get('predicate','')[:16]:16} | {t.get('object','')[:38]:38} "
              f"| {t.get('subject_type')}/{t.get('object_type')}")
        shown += 1
        if shown >= 12:
            break

print("\n--- 4 observation records ---")
shown = 0
for t in new:
    if str(t.get("object", "")).startswith("obs-"):
        print(json.dumps({k: t[k] for k in ("subject", "predicate", "object", "property", "value_raw",
                                            "value", "unit", "conditions", "paper_id") if k in t},
                         ensure_ascii=False)[:400])
        shown += 1
        if shown >= 4:
            break
