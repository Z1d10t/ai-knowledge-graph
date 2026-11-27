import json
import os
import re

ROOT = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\ai-knowledge-graph-main"
PRED = os.path.join(ROOT, "evaluation", "kg_output_eval", "enriched")

targets = {
    "201_Jeong_2021_Pseudo-halide-anion-engineering-for-α-FAPbI3-per": ["grain", "μm", "um", "2 μ"],
    "066_Liu_2022_A-near-infrared-colloidal-quantum-dot-imager-wit": ["640", "512", "dark current", "490"],
    "095_Liu_2021_A-wafer-scale-van-der-Waals-dielectric-made-from": ["mv", "180", "resistiv", "capacit"],
}

for pid, needles in targets.items():
    p = os.path.join(PRED, pid + ".json")
    if not os.path.exists(p):
        print("missing", pid)
        continue
    t = json.load(open(p, encoding="utf-8"))
    print("=" * 90)
    print(pid[:50], "triples:", len(t))
    shown = 0
    for x in t:
        blob = f"{x.get('subject')} {x.get('object')} {x.get('value_raw')}".lower()
        if any(n in blob for n in needles):
            print(f"  {str(x.get('subject'))[:42]:42} | {str(x.get('predicate'))[:16]:16} | "
                  f"{str(x.get('object'))[:34]:34} | prop={x.get('property')} val={x.get('value')} unit={x.get('unit')}")
            shown += 1
            if shown >= 12:
                break
    if shown == 0:
        print("  (no matching triples)")
