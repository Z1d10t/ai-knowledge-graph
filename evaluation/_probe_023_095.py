import json
import os

ROOT = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\ai-knowledge-graph-main"
ENR = os.path.join(ROOT, "evaluation", "kg_output_eval", "enriched")

for pref, needles in (("023", ["5 × 10", "5x10", "3 × 10", "dislocation"]),
                      ("095", ["10^9", "1.15", "resistiv", "capacit"])):
    f = [x for x in os.listdir(ENR) if x.startswith(pref)][0]
    t = json.load(open(os.path.join(ENR, f), encoding="utf-8"))
    print("=" * 80)
    print(f[:60], "triples:", len(t))
    hit = 0
    for x in t:
        blob = f"{x.get('subject')} {x.get('object')} {x.get('value_raw')} {x.get('property')}".lower()
        if any(n.lower() in blob for n in needles):
            print(f"  {str(x.get('subject'))[:36]:36} | {str(x.get('predicate'))[:14]:14} | "
                  f"{str(x.get('object'))[:34]:34} | prop={x.get('property')} val={x.get('value')} unit={x.get('unit')}")
            hit += 1
            if hit >= 8:
                break
    if not hit:
        print("  (none)")
