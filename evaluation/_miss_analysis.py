import csv
import json
import os
import re

ROOT = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\ai-knowledge-graph-main"
SEED = os.path.join(ROOT, "evaluation", "ai_expert_seed_10")
PRED = os.path.join(ROOT, "evaluation", "kg_output_eval", "enriched")

rows = list(csv.DictReader(open(os.path.join(ROOT, "evaluation", "expert_seed_matches.csv"), encoding="utf-8-sig")))


def load(pid):
    p = os.path.join(PRED, pid + ".json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []


print("missed / partial facts and whether the value or object exists anywhere in the predictions\n")
for r in rows:
    if int(r["tier"]) >= 2:
        continue
    pid = None
    for name in os.listdir(SEED):
        if name.startswith(r["paper"].split("_")[0]) and name.endswith("_expert.csv"):
            pid = name[:-len("_expert.csv")]
            break
    pred = load(pid) if pid else []
    blob = " ".join(f"{t.get('subject')} {t.get('object')} {t.get('value_raw') or ''}" for t in pred).lower()

    probe = str(r["gold_value"] or "").strip()
    found_val = probe and probe.lower() in blob
    obj_probe = str(r["gold_object"] or "").strip()[:40].lower()
    found_obj = obj_probe and obj_probe in blob
    print(f"[{r['paper'][:3]}] {r['fact_id']} tier={r['tier']}")
    print(f"    gold : {r['gold_subject']} | {r['gold_predicate']} | {r['gold_object']} "
          f"| prop={r['gold_property']} val={r['gold_value']}{r['gold_unit']}")
    print(f"    value in predictions: {bool(found_val)} | object text in predictions: {bool(found_obj)}")
