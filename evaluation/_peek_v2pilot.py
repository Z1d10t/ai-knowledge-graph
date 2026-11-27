import json
import os
from collections import Counter

D = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\ai-knowledge-graph-main\evaluation\v2pilot\out\enriched"
triples = []
for f in sorted(os.listdir(D)):
    triples += json.load(open(os.path.join(D, f), encoding="utf-8"))

obs = [t for t in triples if str(t.get("object", "")).startswith("obs-")]
print("triples", len(triples), "obs", len(obs))
print("value_type:", Counter(t.get("value_type") for t in obs))
print("condition_status:", Counter(t.get("condition_status") for t in obs))
print("with conditions:", sum(1 for t in obs if t.get("conditions")),
      f"({sum(1 for t in obs if t.get('conditions'))/max(1,len(obs)):.1%})")
print("sample_id unstated:", sum(1 for t in obs if str(t.get("sample_id")).lower() == "unstated"))
print("source_study:", sum(1 for t in obs if t.get("source_study")))
print("conditions_source:", Counter(t.get("conditions_source") for t in obs))
print("\nsample observations:")
for t in obs[:10]:
    print(f"  {str(t.get('subject'))[:32]:32} | {str(t.get('property'))[:26]:26} | {t.get('value')} {t.get('unit')} "
          f"| type={t.get('value_type')} | cond={t.get('conditions')}")
