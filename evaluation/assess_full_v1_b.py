# -*- coding: utf-8 -*-
"""Second-pass quality probes: generic hubs, duplicate measurements, conditions."""
import json
import os
import random
import re
from collections import Counter

BASE = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\ai-knowledge-graph-main\evaluation\full_v1\kg_output\enriched"
random.seed(11)

triples = []
for f in sorted(os.listdir(BASE)):
    if f.endswith(".json"):
        triples += json.load(open(os.path.join(BASE, f), encoding="utf-8"))

GENERIC = {"device", "devices", "control device", "perovskite film", "perovskite films", "film", "films",
           "sample", "samples", "pscs", "perovskite", "material", "materials", "cell", "cells"}

generic_edges = [t for t in triples if str(t.get("subject", "")).strip().lower() in GENERIC]
print(f"[A] edges whose subject is a generic hub: {len(generic_edges)} ({len(generic_edges)/len(triples):.1%})")
print("   top generic subjects:", Counter(str(t.get("subject")).lower() for t in generic_edges).most_common(8))

# duplicate measurements (same subject + property + value + unit)
obs = [t for t in triples if str(t.get("object", "")).startswith("obs-")]
keys = Counter((str(t.get("subject")).lower(), str(t.get("property")).lower(),
                str(t.get("value")), str(t.get("unit"))) for t in obs)
dups = {k: v for k, v in keys.items() if v > 1}
print(f"\n[B] observation edges={len(obs)} unique measurements={len(keys)} duplicated groups={len(dups)} "
      f"({sum(dups.values())} edges involved)")
for k, v in list(dups.items())[:5]:
    print("   ", k, "x", v)

# conditions by property
by_prop = Counter(str(t.get("property")).lower() for t in obs)
with_cond = Counter(str(t.get("property")).lower() for t in obs if t.get("conditions"))
print("\n[C] conditions coverage by property (top 8):")
for p, c in by_prop.most_common(8):
    print(f"   {p[:44]:44} {with_cond.get(p,0):5}/{c:<5} = {with_cond.get(p,0)/c:.0%}")

# review-paper sample
rev = [t for t in triples if t.get("document", "").startswith("153") or False]
print("\n[D] sample from a high-density review (153):")
m153 = [f for f in os.listdir(BASE) if f.startswith("153")][0]
p153 = json.load(open(os.path.join(BASE, m153), encoding="utf-8"))
for t in random.sample(p153, min(10, len(p153))):
    print(f"   {str(t.get('subject'))[:36]:36} | {str(t.get('predicate'))[:14]:14} | {str(t.get('object'))[:40]:40}")

# verbose objects
long_obj = [t for t in triples if len(str(t.get("object"))) > 120]
print(f"\n[E] triples with object >120 chars: {len(long_obj)} ({len(long_obj)/len(triples):.1%})")
for t in long_obj[:3]:
    print("   ", str(t.get("object"))[:130])
