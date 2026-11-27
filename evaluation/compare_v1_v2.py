# -*- coding: utf-8 -*-
"""Compare full_v1 and full_v2 on structure and measurement quality."""
import json
import os
from collections import Counter

ROOT = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\ai-knowledge-graph-main\evaluation"
RUNS = {"v1": os.path.join(ROOT, "full_v1", "kg_output", "enriched"),
        "v2": os.path.join(ROOT, "full_v2", "kg_output", "enriched")}


def load(d):
    triples = []
    if not os.path.isdir(d):
        return triples
    for f in sorted(os.listdir(d)):
        if f.endswith(".json"):
            triples += json.load(open(os.path.join(d, f), encoding="utf-8"))
    return triples


def stats(triples, label):
    n = len(triples)
    obs = [t for t in triples if str(t.get("object", "")).startswith("obs-")]
    with_cond = [t for t in obs if t.get("conditions")]
    unstated = sum(1 for t in obs if str(t.get("sample_id")).lower() == "unstated")
    vt = Counter(t.get("value_type") for t in obs)
    cs = Counter(t.get("condition_status") for t in obs)
    src_study = sum(1 for t in obs if t.get("source_study"))
    ev = [t for t in triples if "evidence_text_match" in t]
    ev_ok = sum(1 for t in ev if t.get("evidence_text_match"))
    dep = sum(1 for t in triples if str(t.get("predicate")) == "depends on")
    unm = sum(1 for t in triples if t.get("unmapped"))
    print(f"\n=== {label} ===")
    print(f"triples {n} | obs {len(obs)} | conditions {len(with_cond)} ({len(with_cond)/max(1,len(obs)):.1%})")
    print(f"condition_status {dict(cs)}")
    print(f"value_type {dict(vt)}")
    print(f"sample_id unstated {unstated} ({unstated/max(1,len(obs)):.1%}) | source_study {src_study}")
    print(f"evidence matched {ev_ok}/{len(ev)} ({ev_ok/max(1,len(ev)):.1%}) | depends on {dep} | unmapped edges {unm}")
    return {"triples": n, "obs": len(obs), "with_conditions": len(with_cond),
            "value_type": dict(vt), "condition_status": dict(cs),
            "sample_unstated": unstated, "source_study": src_study,
            "evidence_matched": ev_ok, "evidence_marked": len(ev), "depends_on": dep, "unmapped": unm}


out = {k: stats(load(v), k) for k, v in RUNS.items()}
json.dump(out, open(os.path.join(ROOT, "compare_v1_v2.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\nwritten evaluation/compare_v1_v2.json")
