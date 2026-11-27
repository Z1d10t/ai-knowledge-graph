# -*- coding: utf-8 -*-
"""Deep assessment of the full_v1 run (92k triples)."""
import json
import os
import random
import re
from collections import Counter, defaultdict

BASE = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\ai-knowledge-graph-main\evaluation\full_v1\kg_output"
ENR = os.path.join(BASE, "enriched")
MD = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\材料论文\全部_285篇\md"

random.seed(7)

papers = {}
for f in sorted(os.listdir(ENR)):
    if f.endswith(".json"):
        papers[f[:-5]] = json.load(open(os.path.join(ENR, f), encoding="utf-8"))

triples = [t for ts in papers.values() for t in ts]
n = len(triples)
print(f"papers={len(papers)} triples={n}")

# ---------- 1. per-paper density ----------
words = {}
for pid in papers:
    p = os.path.join(MD, pid + ".md")
    if os.path.exists(p):
        words[pid] = len(open(p, encoding="utf-8").read().split())
dens = [(pid, len(ts), words.get(pid, 0), 1000 * len(ts) / max(1, words.get(pid, 1)))
        for pid, ts in papers.items()]
dens.sort(key=lambda x: -x[3])
print("\n[1] density (triples per 1000 words) top 5:")
for d in dens[:5]:
    print(f"   {d[0][:44]:44} {d[1]:5} triples / {d[2]:6} words = {d[3]:6.1f}")
print("   bottom 3:")
for d in dens[-3:]:
    print(f"   {d[0][:44]:44} {d[1]:5} triples / {d[2]:6} words = {d[3]:6.1f}")
print(f"   median density: {sorted(x[3] for x in dens)[len(dens)//2]:.1f}")

# ---------- 2. entity duplication ----------
subs = Counter(str(t.get("subject")) for t in triples)
ents = set(subs) | {str(t.get("object")) for t in triples if not str(t.get("object", "")).startswith("obs-")}
by_lower = defaultdict(set)
for e in ents:
    by_lower[e.lower()].add(e)
dups = {k: v for k, v in by_lower.items() if len(v) > 1}
print(f"\n[2] entities={len(ents)} unique-case-groups={len(by_lower)} case-variant groups={len(dups)}")
for k, v in list(dups.items())[:8]:
    print("   ", sorted(v)[:4])

# ---------- 3. measurement completeness ----------
obs_edges = [t for t in triples if str(t.get("object", "")).startswith("obs-")]
with_val = [t for t in obs_edges if t.get("value") is not None]
with_unit = [t for t in obs_edges if t.get("unit")]
with_prop = [t for t in obs_edges if t.get("property")]
with_cond = [t for t in obs_edges if t.get("conditions")]
print(f"\n[3] observation edges={len(obs_edges)}")
print(f"   value {len(with_val)} ({len(with_val)/max(1,len(obs_edges)):.1%}) | unit {len(with_unit)} "
      f"({len(with_unit)/max(1,len(obs_edges)):.1%}) | property {len(with_prop)} ({len(with_prop)/max(1,len(obs_edges)):.1%}) "
      f"| conditions {len(with_cond)} ({len(with_cond)/max(1,len(obs_edges)):.1%})")

# ---------- 4. depends on ----------
dep = [t for t in triples if str(t.get("predicate")) == "depends on"]
print(f"\n[4] 'depends on' edges={len(dep)}; sample:")
for t in random.sample(dep, min(8, len(dep))):
    print(f"   {str(t.get('subject'))[:36]:36} → {str(t.get('object'))[:40]:40} | ev={str(t.get('evidence_text_match'))}")

# ---------- 5. unmapped ----------
unm = Counter(str(t.get("predicate")) for t in triples if t.get("unmapped"))
print(f"\n[5] unmapped types={len(unm)} edges={sum(unm.values())}; top 15:")
print("   ", ", ".join(f"{k}:{v}" for k, v in unm.most_common(15)))

# ---------- 6. evidence ----------
ev = [t for t in triples if "evidence_text_match" in t]
ok = sum(1 for t in ev if t.get("evidence_text_match"))
no_src = sum(1 for t in triples if not t.get("source"))
lens = [len(str(t.get("source") or "")) for t in triples if t.get("source")]
print(f"\n[6] evidence rows={len(ev)} match={ok} ({ok/max(1,len(ev)):.1%}) | no source={no_src} "
      f"| source len median={sorted(lens)[len(lens)//2] if lens else 0}")

# ---------- 7. structural checks ----------
self_loops = sum(1 for t in triples if t.get("subject") == t.get("object"))
num_subjects = sum(1 for t in triples if re.fullmatch(r"[\d.\s%±<>~-]+", str(t.get("subject"))))
print(f"\n[7] self loops={self_loops} | numeric subjects={num_subjects}")

# ---------- 8. top entities ----------
print("\n[8] top 10 entities by outgoing edges:")
for e, c in subs.most_common(10):
    print(f"   {e[:56]:56} {c}")

# ---------- 9. random triples ----------
print("\n[9] 12 random extracted triples:")
sample = [t for t in triples if not t.get("inferred") and not str(t.get("object", "")).startswith("obs-")]
for t in random.sample(sample, 12):
    print(f"   {str(t.get('subject'))[:34]:34} | {str(t.get('predicate'))[:16]:16} | {str(t.get('object'))[:34]:34} "
          f"| {t.get('subject_type')}/{t.get('object_type')}")
