# -*- coding: utf-8 -*-
"""Quality report for the 10-paper pilot run."""
import json
import os
import re
import collections

OUT = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\ai-knowledge-graph-main\article\extracted\semiconductor_pilot\kg_output"
ENR = os.path.join(OUT, "enriched")
RAW = os.path.join(OUT, "raw")

rows = []
types = collections.Counter()
preds = collections.Counter()
noise_pred = collections.Counter()
num_triples = 0
self_loops = 0
inferred_by_method = collections.Counter()
edges_with_source = 0
total = 0
samples = []
material_like = []

for f in sorted(os.listdir(ENR)):
    t = json.load(open(os.path.join(ENR, f), encoding="utf-8"))
    raw = json.load(open(os.path.join(RAW, f), encoding="utf-8"))
    n_inf = sum(1 for x in t if x.get("inferred"))
    nodes = len({x["subject"] for x in t} | {x["object"] for x in t})
    rows.append((f.split("_")[0], len(raw), len(t), n_inf, nodes))
    for x in t:
        total += 1
        types[x.get("subject_type")] += 1
        types[x.get("object_type")] += 1
        preds[x["predicate"]] += 1
        if x.get("inferred"):
            inferred_by_method[x.get("method")] += 1
        else:
            if x.get("source"):
                edges_with_source += 1
        if x["subject"] == x["object"]:
            self_loops += 1
        if re.search(r"\d", x["subject"] + " " + x["object"]):
            num_triples += 1
        p = x["predicate"]
        if p in ("authored", "published in", "affiliated with", "supervised", "wrote"):
            noise_pred[p] += 1
        if x.get("subject_type") in ("technology", "product", "concept") and len(samples) < 40:
            samples.append((f[:3], x["subject"], p, x["object"], x.get("subject_type"), x.get("object_type")))

print("paper  raw   enriched  inferred  nodes")
for r in rows:
    print(f"{r[0]:>5}  {r[1]:>5}  {r[2]:>8}  {r[3]:>8}  {r[4]:>5}")
print(f"TOTAL  {sum(r[1] for r in rows):>5}  {total:>8}  {sum(r[3] for r in rows):>8}")

print("\n--- entity type distribution (subject+object) ---")
for k, v in types.most_common():
    print(f"  {str(k):16} {v:6}  {v / (2 * total):6.1%}")

print("\n--- top 20 predicates ---")
for k, v in preds.most_common(20):
    print(f"  {k:22} {v:6}")
print(f"  unique predicates: {len(preds)}")

print("\n--- noise / quality ---")
print("  bibliographic predicates:", dict(noise_pred), "=", sum(noise_pred.values()), f"({sum(noise_pred.values())/total:.1%})")
print("  person/org/place share:", f"{(types['person']+types['organization']+types['place'])/(2*total):.1%}")
print("  triples mentioning a number:", num_triples, f"({num_triples/total:.1%})")
print("  self loops:", self_loops)
print("  extracted edges with source sentence:", edges_with_source, f"({edges_with_source/max(1,total-sum(r[3] for r in rows)):.1%})")
print("  inferred by method:", dict(inferred_by_method))

print("\n--- 18 sample triples (technology/product/concept subjects) ---")
for s in samples[:18]:
    print(f"  [{s[0]}] {s[1][:58]:58} | {s[2][:18]:18} | {s[3][:44]:44} | {s[4]}/{s[5]}")
