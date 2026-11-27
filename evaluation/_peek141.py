import json

p = (r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\ai-knowledge-graph-main\evaluation"
     r"\kg_output_eval\enriched\141_Cheng_2022_High-thermal-conductivity-in-wafer-scale-cubic-s.json")
t = json.load(open(p, encoding="utf-8"))
print("total", len(t))
n = 0
for x in t:
    s = str(x.get("subject", "")) + " " + str(x.get("object", ""))
    if "thermal" in s.lower() or "sic" in s.lower():
        n += 1
        if n <= 25:
            print(f"{str(x.get('subject'))[:38]:38} | {str(x.get('predicate'))[:22]:22} | "
                  f"{str(x.get('object'))[:30]:30} | {x.get('value_raw')} {x.get('unit')} "
                  f"{'U' if x.get('unmapped') else ''}")
print("rows with sic/thermal:", n)
print("unmapped predicates:", sorted({str(x.get("predicate")) for x in t if x.get("unmapped")}))
