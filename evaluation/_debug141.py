import csv
import json
import os
import sys

ROOT = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\ai-knowledge-graph-main"
sys.path.insert(0, os.path.join(ROOT, "evaluation"))
sys.path.insert(0, os.path.join(ROOT, "src"))
import evaluate as E  # noqa: E402

pid = "141_Cheng_2022_High-thermal-conductivity-in-wafer-scale-cubic-s"
gold = E.read_gold(os.path.join(ROOT, "evaluation", "gold", pid + ".csv"))
pred = json.load(open(os.path.join(ROOT, "evaluation", "kg_output_eval", "enriched", pid + ".json"),
                      encoding="utf-8"))
pk, _ = E.pred_keys(pred, 2)
gk = {E.gold_key(r): r for r in gold if str(r.get("in_scope", "1")) not in ("0", "")}

print("gold keys:")
for k, row in gk.items():
    hit = k in pk
    print(("  HIT  " if hit else "  MISS ") + f"{k}   [{row['subject']} | {row.get('predicate_canonical')} | {row.get('object')}]")

print("\nnearby predictions (thermal/SiC, chunk<=2):")
for t in pred:
    if int(t.get("chunk") or 0) > 2:
        continue
    s = f"{t.get('subject')} {t.get('object')}".lower()
    if "sic" in s or "thermal" in s or "power electronics" in s:
        print("   ", t.get("subject"), "|", t.get("predicate"), "|", t.get("object"),
              "|", t.get("property"), t.get("value"), t.get("unit"))
