# -*- coding: utf-8 -*-
"""Merge the two parallel v2 halves into evaluation/full_v2/kg_output."""
import csv
import json
import os
import shutil

ROOT = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\ai-knowledge-graph-main\evaluation"
PARTS = [os.path.join(ROOT, "v2_a", "kg_output"), os.path.join(ROOT, "v2_b", "kg_output")]
OUT = os.path.join(ROOT, "full_v2", "kg_output")

for sub in ("raw", "enriched", "failures"):
    os.makedirs(os.path.join(OUT, sub), exist_ok=True)

copied = 0
rows = []
for part in PARTS:
    for sub in ("raw", "enriched"):
        d = os.path.join(part, sub)
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.endswith(".json"):
                shutil.copy2(os.path.join(d, f), os.path.join(OUT, sub, f))
                if sub == "enriched":
                    copied += 1
    fdir = os.path.join(part, "failures")
    if os.path.isdir(fdir):
        for f in os.listdir(fdir):
            shutil.copy2(os.path.join(fdir, f), os.path.join(OUT, "failures", f))
    s = os.path.join(part, "summary.csv")
    if os.path.exists(s):
        rows += list(csv.DictReader(open(s, encoding="utf-8-sig")))

seen, uniq = set(), []
for r in rows:
    if r["id"] in seen:
        continue
    seen.add(r["id"])
    uniq.append(r)

if uniq:
    fields = list(uniq[0].keys())
    with open(os.path.join(OUT, "summary.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(uniq, key=lambda r: r["id"]))
    # summary.json is what --re-enrich reads back to preserve run counters
    json.dump({r["id"]: r for r in uniq},
              open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

print(f"papers merged: {copied} | summary rows: {len(uniq)}")
print(f"failed papers: {sum(1 for r in uniq if int(r.get('empty_failed') or 0) > 0)}")
print(f"failed chunks: {sum(int(r.get('empty_failed') or 0) for r in uniq)}")
