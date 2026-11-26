# -*- coding: utf-8 -*-
"""Build the frozen 30-paper gold-standard set (stratified, disjoint from dev/blind).

Dev set   : 1,30,60,90,120,150,180,210,240,270   (prompt tuning)
Exploratory: 45,75,135,195,255                   (results already seen -> not final eval)
Gold set  : 30 papers, stratified by direction and paper type, frozen before annotation.
"""
import csv
import json
import os
import re
from collections import defaultdict

ROOT = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目"
CORPUS = os.path.join(ROOT, "材料论文", "全部_285篇")
EVAL = os.path.join(ROOT, "ai-knowledge-graph-main", "evaluation")
os.makedirs(EVAL, exist_ok=True)

DEV = {1, 30, 60, 90, 120, 150, 180, 210, 240, 270}
EXPLORE = {45, 75, 135, 195, 255}

ROWS = list(csv.DictReader(open(os.path.join(CORPUS, "索引_285篇.csv"), encoding="utf-8-sig")))

DIRECTION_PATTERNS = [
    ("perovskite", r"perovskite|fapbi|mapbi|cspbi|halide"),
    ("2d", r"\b2d\b|two-dimensional|mos2|graphene|tmd|transition[- ]metal dichalcogenide|van der waals|monolayer|mxene"),
    ("organic-flex", r"organic semiconductor|polymer|flexible|stretchable|wearable|electrochemical transistor"),
    ("quantum-dot", r"quantum dot|quantum-dots|\bqds?\b|nanocrystal"),
    ("wide-bandgap", r"\bgan\b|gallium nitride|\bsic\b|silicon carbide|ga2o3|wide[- ]band[- ]?gap|\bwbg\b|algan|ultraviolet|deep[- ]uv"),
    ("memory-device", r"memristor|neuromorphic|ferroelectric|synapse|transistor"),
]
REVIEW_RE = re.compile(r"\breview\b|\bperspective\b|\bprogress\b|\badvances\b|\boverview\b|tutorial", re.I)
THEORY_RE = re.compile(r"\bdft\b|first[- ]principles|density functional|simulation|theoretical|ab initio|"
                       r"monte carlo|molecular dynamics", re.I)
REVIEW_VENUES = {"chemical reviews", "chemical society reviews", "materials today", "nature reviews materials"}


def direction(row):
    text = (row["标题"] + " " + row["期刊"]).lower()
    for name, pat in DIRECTION_PATTERNS:
        if re.search(pat, text, re.I):
            return name
    return "other"


def paper_type(row):
    if REVIEW_RE.search(row["标题"]) or row["期刊"].strip().lower() in REVIEW_VENUES:
        return "review"
    if THEORY_RE.search(row["标题"]):
        return "theory"
    return "experimental"


pool = []
for r in ROWS:
    n = int(r["统一编号"])
    if n in DEV or n in EXPLORE:
        continue
    pool.append({
        "num": n,
        "title": r["标题"],
        "venue": r["期刊"],
        "year": r["年份"],
        "cite": int(r["引用量"] or 0),
        "doi": r["DOI"],
        "md": r["MD 文件"],
        "direction": direction(r),
        "type": paper_type(r),
    })

by_dir = defaultdict(list)
for p in pool:
    by_dir[p["direction"]].append(p)

QUOTA = {"perovskite": 8, "2d": 8, "wide-bandgap": 6, "quantum-dot": 5, "organic-flex": 2, "memory-device": 1}


def pick(items, k):
    """Deterministic spread: sort by citations, take evenly spaced entries, prefer review+theory."""
    items = sorted(items, key=lambda x: -x["cite"])
    if len(items) <= k:
        return items
    step = len(items) / k
    return [items[int(i * step)] for i in range(k)]


selected = []
for d, k in QUOTA.items():
    items = by_dir.get(d, [])
    chosen = pick(items, k)
    # make sure at least one review and one theory where available
    for wanted in ("review", "theory"):
        if not any(p["type"] == wanted for p in chosen):
            cand = [p for p in items if p["type"] == wanted and p not in chosen]
            if cand:
                chosen[-1] = cand[0]
    selected.extend(chosen)

# top up to 30 from the remaining pool, evenly across directions
if len(selected) < 30:
    rest = [p for p in pool if p not in selected]
    selected.extend(pick(rest, 30 - len(selected)))

selected = selected[:30]
selected.sort(key=lambda p: p["num"])

out = os.path.join(EVAL, "eval_set_30.json")
json.dump(selected, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
with open(os.path.join(EVAL, "eval_set_30.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(selected[0].keys()))
    w.writeheader()
    w.writerows(selected)

print(f"selected {len(selected)} papers -> {out}")
from collections import Counter
print("directions:", Counter(p["direction"] for p in selected))
print("types     :", Counter(p["type"] for p in selected))
print("years     :", Counter(p["year"] for p in selected))
for p in selected:
    print(f"  {p['num']:3d} {p['direction']:13} {p['type']:12} {p['year']} {p['cite']:5} {p['venue'][:26]:26} {p['title'][:54]}")
