# -*- coding: utf-8 -*-
"""v2 quality checks: 28-fact strict structured match, depends-on evidence, duplicates."""
import csv
import json
import os
import re
from collections import Counter
from difflib import SequenceMatcher

ROOT = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\ai-knowledge-graph-main"
SEED = os.path.join(ROOT, "evaluation", "ai_expert_seed_10")
RUN = os.environ.get("RUN", "full_v2")
ENR = os.path.join(ROOT, "evaluation", RUN, "kg_output", "enriched")


def norm(s):
    return re.sub(r"[^a-z0-9%+\-.]+", " ", str(s or "").lower()).strip()


def num(v):
    m = re.search(r"[-+]?\d+(?:\.\d+)?", str(v or ""))
    if not m:
        return ""
    try:
        return "%g" % float(m.group(0))
    except ValueError:
        return ""


def sim(a, b):
    na, nb = norm(a), norm(b)
    if na == nb:
        return 1.0
    if na in nb or nb in na:
        return 0.9
    return SequenceMatcher(None, na, nb).ratio()


papers = {}
for f in os.listdir(ENR):
    if f.endswith(".json"):
        papers[f[:-5]] = json.load(open(os.path.join(ENR, f), encoding="utf-8"))

strict = partial = missing = 0
rows = []
for name in sorted(os.listdir(SEED)):
    if not name.endswith("_expert.csv"):
        continue
    pid = name[:-len("_expert.csv")]
    pred = papers.get(pid, [])
    with open(os.path.join(SEED, name), encoding="utf-8-sig", newline="") as f:
        for g in csv.DictReader(f):
            if not g.get("subject"):
                continue
            q = num(g.get("value"))
            best = None
            for t in pred:
                if not str(t.get("object", "")).startswith("obs-"):
                    continue
                if q and num(t.get("value")) != q:
                    continue
                if not q:
                    continue
                s = sim(t.get("subject"), g["subject"])
                p = sim(t.get("property"), g.get("property"))
                u = (str(t.get("unit") or "").lower() == str(g.get("unit") or "").lower())
                if s >= 0.6 and p >= 0.5:
                    best = (t, s, p, u)
                    break
            if best:
                t, s, p, u = best
                need_cond = bool(str(g.get("conditions") or "").strip())
                ok = (s >= 0.6 and p >= 0.5 and u and (bool(t.get("conditions")) or not need_cond))
                if ok:
                    strict += 1
                else:
                    partial += 1
                rows.append([g["fact_id"], "structured", round(s, 2), round(p, 2), u, bool(t.get("conditions"))])
            else:
                missing += 1
                rows.append([g["fact_id"], "missing", "", "", "", ""])

print("28 facts vs v2: strict(structured+property+unit+conditions) =", strict,
      "| partial =", partial, "| missing =", missing)

# depends on evidence
dep = [t for p in papers.values() for t in p if str(t.get("predicate")) == "depends on"]
ev = [t for t in dep if "evidence_text_match" in t]
print(f"depends on: {len(dep)} | with evidence marker {len(ev)} | matched {sum(1 for t in ev if t.get('evidence_text_match'))}")

# duplicates after dedupe
obs = [t for p in papers.values() for t in p if str(t.get("object", "")).startswith("obs-")]
key = Counter((str(t.get("subject")).lower(), str(t.get("property")).lower(), str(t.get("value")),
               str(t.get("unit")), json.dumps(t.get("conditions"), sort_keys=True, ensure_ascii=False))
              for t in obs)
dups = {k: v for k, v in key.items() if v > 1}
print(f"duplicate observation groups after v2 dedupe: {len(dups)} ({sum(dups.values())} edges)")

json.dump({"strict": strict, "partial": partial, "missing": missing, "rows": rows,
           "depends_on": len(dep), "depends_on_evidence": len(ev),
           "dup_groups": len(dups)}, open(os.path.join(ROOT, "evaluation", RUN, "quality_check.json"),
                                          "w", encoding="utf-8"), ensure_ascii=False, indent=1)
