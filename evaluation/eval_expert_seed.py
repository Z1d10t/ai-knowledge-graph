# -*- coding: utf-8 -*-
"""Evaluate the 28 expert seed facts against the materials-profile predictions.

The seed set is NOT exhaustive, so precision against it is meaningless. What is
reported here:
  * coverage   - how many expert facts the pipeline reproduces (tiered matching)
  * tier       - 1 strict / 2 relaxed subject / 3 value-only or miss
  * field diff - for each matched fact, which fields disagreed

Usage:
    python evaluation/eval_expert_seed.py
Outputs evaluation/expert_seed_eval.json / .csv
"""
import csv
import json
import os
import re
import sys
from difflib import SequenceMatcher

ROOT = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\ai-knowledge-graph-main"
sys.path.insert(0, os.path.join(ROOT, "src"))
from knowledge_graph.postprocess.quantities import canon_unit  # noqa: E402

SEED = os.path.join(ROOT, "evaluation", "ai_expert_seed_10")
PRED = os.environ.get("PRED_DIR") or os.path.join(ROOT, "evaluation", "kg_output_eval", "enriched")
OUT_JSON = os.path.join(ROOT, "evaluation", "expert_seed_eval.json")
OUT_CSV = os.path.join(ROOT, "evaluation", "expert_seed_matches.csv")
OBS = re.compile(r"^obs-")


def norm(s):
    s = str(s or "").lower().strip()
    s = re.sub(r"[^a-z0-9%+\-.]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def unit_norm(u):
    s = str(canon_unit(u) or "").lower().strip()
    s = s.replace("µ", "u").replace("μ", "u").replace("∙", "·").replace("ohm", "Ω")
    s = re.sub(r"\s+", "", s)
    return s


def num(v):
    """Pull a comparable number out of '5e8cm^-2', '10^9', '>24%', '1.75 mS/um' ..."""
    s = str(v or "").strip().lower().replace(" ", "")
    if not s:
        return ""
    m = re.search(r"10\^(\d+)", s)
    if m:
        return "%g" % (10 ** int(m.group(1)))
    m = re.search(r"(\d+(?:\.\d+)?(?:e[+-]?\d+)?)", s)
    if not m:
        return ""
    try:
        return "%g" % float(m.group(1))
    except ValueError:
        return ""


def subject_sim(a, b):
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    if na in nb or nb in na:
        return 0.9
    ta, tb = set(na.split()), set(nb.split())
    jac = len(ta & tb) / max(1, len(ta | tb))
    return max(jac, SequenceMatcher(None, na, nb).ratio() * 0.9)


def load_pred(pid):
    p = os.path.join(PRED, pid + ".json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []


def fact_triples(pred):
    """Facts only: observation edges (subject -> obs) plus plain relations."""
    out = []
    for t in pred:
        if OBS.match(str(t.get("subject"))):
            continue
        if OBS.match(str(t.get("object"))):
            out.append({"kind": "measurement", "subject": t.get("subject"),
                        "property": t.get("property"), "value": t.get("value"),
                        "unit": t.get("unit"), "raw": t.get("value_raw"), "chunk": t.get("chunk")})
        else:
            out.append({"kind": "relation", "subject": t.get("subject"),
                        "predicate": t.get("predicate"), "object": t.get("object"),
                        "chunk": t.get("chunk")})
    return out


def sim(a, b):
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def match(gold, facts):
    """Return (tier, matched_fact, detail). Tier 1 strict, 2 relaxed subject, 3 value only, 0 miss."""
    gt = norm(gold.get("predicate_canonical"))
    if gold.get("property") or gold.get("value_raw"):
        gv, gu = num(gold.get("value") or gold.get("value_raw")), unit_norm(gold.get("unit"))
        if not gu:  # some rows fold the unit into value_raw
            gu = unit_norm(re.sub(r"^[\d.eE+\-x×^]+", "", str(gold.get("value_raw") or "")))
        gs = norm(gold.get("subject"))
        best = None
        for f in facts:
            if f["kind"] != "measurement":
                continue
            if num(f.get("value")) != gv or not gv:
                continue
            s = subject_sim(f["subject"], gold["subject"])
            ok_unit = (not gu) or (unit_norm(f.get("unit")) == gu)
            if s >= 0.6 and ok_unit:
                return 1, f, ""
            if s >= 0.5:
                best = best or (3, f, f"subject/unit '{f['subject']}' {f.get('unit')} vs '{gold['subject']}' {gold.get('unit')}")
            elif best is None:
                best = (3, f, f"value found on '{f['subject']}'")
        return best or (0, None, "")
    go, gs = norm(gold.get("object")), norm(gold.get("subject"))
    for f in facts:
        if f["kind"] != "relation":
            continue
        same_obj = norm(f["object"]) == go or go in norm(f["object"]) or norm(f["object"]) in go
        if norm(f["predicate"]) == gt and same_obj and norm(f["subject"]) == gs:
            return 1, f, ""
        if norm(f["predicate"]) == gt and same_obj and subject_sim(f["subject"], gold["subject"]) >= 0.6:
            return 2, f, f"subject '{f['subject']}' vs '{gold['subject']}'"
    for f in facts:
        if f["kind"] == "relation" and norm(f["object"]) == go and subject_sim(f["subject"], gold["subject"]) >= 0.6:
            return 3, f, f"predicate '{f['predicate']}' vs '{gt}'"
    return 0, None, ""


rows, tiers = [], {0: 0, 1: 0, 2: 0, 3: 0}
per_paper = {}
for name in sorted(os.listdir(SEED)):
    if not name.endswith("_expert.csv"):
        continue
    pid = name[:-len("_expert.csv")]
    pred = load_pred(pid)
    facts = fact_triples(pred)
    with open(os.path.join(SEED, name), encoding="utf-8-sig", newline="") as f:
        gold_rows = [r for r in csv.DictReader(f) if r.get("subject")]
    hit = 0
    for g in gold_rows:
        tier, f, detail = match(g, facts)
        tiers[tier] += 1
        hit += int(tier > 0)
        rows.append({
            "paper": pid[:40], "fact_id": g["fact_id"], "tier": tier,
            "gold_subject": g["subject"], "gold_predicate": g.get("predicate_canonical"),
            "gold_object": g["object"], "gold_property": g.get("property"),
            "gold_value": g.get("value"), "gold_unit": g.get("unit"),
            "gold_conditions": (g.get("conditions") or "")[:120],
            "matched_subject": (f or {}).get("subject", ""),
            "matched_predicate": (f or {}).get("predicate", ""),
            "matched_object": (f or {}).get("raw") or (f or {}).get("object", ""),
            "matched_property": (f or {}).get("property", ""),
            "matched_value": (f or {}).get("value", ""),
            "matched_unit": (f or {}).get("unit", ""),
            "detail": detail,
        })
    per_paper[pid[:40]] = {"gold": len(gold_rows), "covered": hit}

total = len(rows)
covered = total - tiers[0]
print(f"expert seed facts      {total}")
print(f"covered (any tier)     {covered} = {covered/total:.1%}")
print(f"  tier1 strict         {tiers[1]}")
print(f"  tier2 relaxed subject{tiers[2]:4}")
print(f"  tier3 value/predicate{tiers[3]:4}")
print(f"  missed               {tiers[0]}")
print("\nper paper:")
for k, v in per_paper.items():
    print(f"  {k:42} {v['covered']}/{v['gold']}")

with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
json.dump({"total": total, "covered": covered, "tiers": tiers, "per_paper": per_paper,
           "rows": rows}, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\nwritten {OUT_CSV}\nwritten {OUT_JSON}")
