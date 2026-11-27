# -*- coding: utf-8 -*-
"""Build a review digest for the 28 expert seed facts.

For each fact: the gold row, the verbatim evidence located in the paper body (with
context), and the predictions of that paper that share the same numeric value.
Output: evaluation/full_v1/review_digest.md (read in slices) + review_cases.json
"""
import csv
import json
import os
import re

ROOT = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\ai-knowledge-graph-main"
SEED = os.path.join(ROOT, "evaluation", "ai_expert_seed_10")
MD = os.path.join(ROOT, "evaluation", "md")
ENR = os.path.join(ROOT, "evaluation", "full_v1", "kg_output", "enriched")
OUT = os.path.join(ROOT, "evaluation", "full_v1", "review_digest.md")
CASES = os.path.join(ROOT, "evaluation", "full_v1", "review_cases.json")


def norm(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def find_context(body, quote, width=280):
    q = norm(quote)
    if not q:
        return None
    # try progressively shorter prefixes (OCR/markup noise at the tail is common)
    for cut in (len(q), 160, 100, 60):
        probe = q[:cut]
        idx = body.lower().find(probe.lower())
        if idx >= 0:
            return norm(body[max(0, idx - width): idx + len(probe) + width])
    return None


def num(v):
    m = re.search(r"[-+]?\d+(?:\.\d+)?", str(v or ""))
    return m.group(0) if m else None


cases = []
for name in sorted(os.listdir(SEED)):
    if not name.endswith("_expert.csv"):
        continue
    pid = name[:-len("_expert.csv")]
    body = open(os.path.join(MD, pid + ".md"), encoding="utf-8").read()
    body = re.sub(r"\s+", " ", body)
    pred = json.load(open(os.path.join(ENR, pid + ".json"), encoding="utf-8"))

    with open(os.path.join(SEED, name), encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r.get("subject")]

    for g in rows:
        q = num(g.get("value"))
        cands = []
        for t in pred:
            if str(t.get("object", "")).startswith("obs-"):
                if q and num(t.get("value")) == q:
                    cands.append(t)
            elif q and num(t.get("object")) == q:
                cands.append(t)
        cases.append({
            "paper": pid,
            "fact_id": g["fact_id"],
            "gold": {k: g.get(k, "") for k in ("subject", "subject_type", "predicate_canonical",
                                               "object", "object_type", "property", "value_raw",
                                               "value", "unit", "comparator", "sample_or_device",
                                               "conditions", "characterization", "evidence_quote",
                                               "origin", "notes")},
            "context": find_context(body, g.get("evidence_quote")),
            "candidates": [{k: t.get(k) for k in ("subject", "predicate", "object", "property", "value",
                                                  "unit", "conditions", "source", "evidence_text_match")}
                           for t in cands[:6]],
        })

json.dump(cases, open(CASES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

lines = []
for i, c in enumerate(cases, 1):
    g = c["gold"]
    lines.append(f"\n## {i}. {c['fact_id']}  ({c['paper'][:34]})\n")
    lines.append(f"- 声称：**{g['subject']}** —{g['predicate_canonical']}→ **{g['object']}**"
                 f"｜property={g['property']} value={g['value']} unit={g['unit']} "
                 f"cond={g['conditions']} | origin={g['origin']}\n")
    lines.append(f"- 证据句：{g['evidence_quote'][:260]}\n")
    lines.append(f"- 原文上下文：{(c['context'] or '（未定位到）')[:560]}\n")
    if c["candidates"]:
        for t in c["candidates"]:
            lines.append(f"- 预测候选：{t.get('subject')} —{t.get('predicate')}→ {t.get('object')} "
                         f"| prop={t.get('property')} val={t.get('value')} unit={t.get('unit')} "
                         f"| evmatch={t.get('evidence_text_match')}\n")
    else:
        lines.append("- 预测候选：无同值候选\n")

open(OUT, "w", encoding="utf-8").write("# 28 条专家事实复核摘要\n" + "".join(lines))
print("cases:", len(cases))
print("digest:", OUT, os.path.getsize(OUT), "bytes")
