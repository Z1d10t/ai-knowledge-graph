# -*- coding: utf-8 -*-
"""Build the human-annotation pack for the 30-paper gold standard.

For every paper it writes
  evaluation/annotate/<id>.md     scope text (abstract -> conclusion, tables kept) with line numbers
  evaluation/gold/<id>.csv        empty gold-standard sheet (schema + one worked example)
  evaluation/candidates/<id>.csv  model output for reference ONLY (never the annotation basis)
and an index workbook evaluation/eval_index.xlsx.
"""
import csv
import json
import os
import re

ROOT = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目"
EVAL = os.path.join(ROOT, "ai-knowledge-graph-main", "evaluation")
MD = os.path.join(EVAL, "md")
PRED = os.path.join(EVAL, "kg_output_eval", "enriched")
ANNOT = os.path.join(EVAL, "annotate")
GOLD = os.path.join(EVAL, "gold")
CAND = os.path.join(EVAL, "candidates")
for d in (ANNOT, GOLD, CAND):
    os.makedirs(d, exist_ok=True)

GOLD_FIELDS = [
    "fact_id", "in_scope", "subject", "subject_type", "predicate_canonical", "predicate_raw",
    "object", "object_type", "property", "value_raw", "value", "unit", "comparator", "uncertainty",
    "sample_or_device", "conditions", "characterization", "evidence_quote", "evidence_location",
    "origin", "merge_error", "unmapped_verdict", "annotator", "notes",
]

EXAMPLE = {
    "fact_id": "EXAMPLE-1", "in_scope": "1", "subject": "4Cl-BZS treated device", "subject_type": "sample",
    "predicate_canonical": "has efficiency", "predicate_raw": "has efficiency",
    "object": "20.1%", "object_type": "measurement", "property": "power conversion efficiency",
    "value_raw": "20.1%", "value": "20.1", "unit": "%", "comparator": "", "uncertainty": "",
    "sample_or_device": "inverted device, 0.05 cm2", "conditions": "AM 1.5G, 1 sun",
    "characterization": "J-V", "evidence_quote": "the device achieved a PCE of 20.1% under AM 1.5G",
    "evidence_location": "Results, p.3", "origin": "stated", "merge_error": "", "unmapped_verdict": "",
    "annotator": "A1", "notes": "example row - delete before annotating",
}

papers = json.load(open(os.path.join(EVAL, "eval_set_30.json"), encoding="utf-8"))


REF_RE = re.compile(r"(?im)^\s*(?:#+\s*)?\*{0,2}\s*(references|bibliography|references and notes|notes and references)\s*\*{0,2}\s*:?\s*$")


def scope_text(text, max_words=6000):
    """Keep the body (abstract -> conclusion) but never the reference list."""
    m = REF_RE.search(text)
    if m and m.start() > len(text) * 0.2:
        text = text[:m.start()]
    words = text.split()
    return " ".join(words[:max_words])


rows = []
for p in papers:
    pid = p["md"][:-3]
    body = open(os.path.join(MD, p["md"]), encoding="utf-8").read()
    scope = scope_text(body)

    header = (f"# 标注范围：{p['num']:03d} {p['title']}\n\n"
              f"- 期刊/年份：{p['venue']} / {p['year']}　方向：{p['direction']}　类型：{p['type']}\n"
              f"- DOI：{p['doi']}\n"
              f"- 标注范围：摘要、结果与讨论、结论、所有结果表格（下文为正文前 6000 词，含表格）\n"
              f"- 标注规则见 evaluation/README_标注规范.md\n\n---\n\n")
    numbered = "\n".join(f"[{i+1:04d}] {line}" for i, line in enumerate(scope.splitlines()))
    open(os.path.join(ANNOT, f"{pid}.md"), "w", encoding="utf-8").write(header + numbered)

    gold_path = os.path.join(GOLD, f"{pid}.csv")
    existing = 0
    if os.path.exists(gold_path):
        with open(gold_path, encoding="utf-8-sig", newline="") as f:
            existing = sum(1 for row in csv.DictReader(f)
                           if row.get("subject") and not str(row.get("fact_id", "")).startswith("EXAMPLE"))
    if not existing:
        with open(gold_path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=GOLD_FIELDS)
            w.writeheader()
            w.writerow(EXAMPLE)

    # model candidates (reference only)
    pred_path = os.path.join(PRED, f"{pid}.json")
    n_cand = 0
    if os.path.exists(pred_path):
        with open(os.path.join(CAND, f"{pid}.csv"), "w", encoding="utf-8-sig", newline="") as f:
            fields = ["subject", "predicate", "object", "subject_type", "object_type", "property",
                      "value_raw", "unit", "conditions", "source", "evidence_text_match"]
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            for t in json.load(open(pred_path, encoding="utf-8")):
                w.writerow({k: t.get(k, "") for k in fields})
                n_cand += 1

    rows.append([p["num"], p["title"], p["venue"], p["year"], p["direction"], p["type"], p["doi"],
                 f"annotate/{pid}.md", f"gold/{pid}.csv", f"candidates/{pid}.csv", n_cand])

from openpyxl import Workbook  # noqa: E402
from openpyxl.styles import Font, PatternFill  # noqa: E402

wb = Workbook()
ws = wb.active
ws.title = "评估集30篇"
head = ["编号", "标题", "期刊", "年份", "方向", "类型", "DOI", "标注范围文件", "金标准表", "模型候选(参考)", "候选条数"]
ws.append(head)
for c in range(1, len(head) + 1):
    ws.cell(row=1, column=c).fill = PatternFill("solid", fgColor="1F3864")
    ws.cell(row=1, column=c).font = Font(color="FFFFFF", bold=True)
for r in rows:
    ws.append(r)
widths = {"A": 7, "B": 60, "C": 24, "D": 7, "E": 14, "F": 13, "G": 34, "H": 44, "I": 44, "J": 46, "K": 10}
for k, v in widths.items():
    ws.column_dimensions[k].width = v
ws.freeze_panes = "B2"

ws2 = wb.create_sheet("标注进度")
ws2.append(["编号", "标注人", "事实条数", "已完成", "复核人", "复核完成", "备注"])
for r in rows:
    ws2.append([r[0], "", 0, "否", "", "否", ""])
ws2.column_dimensions["A"].width = 8
for k in "BCDEFG":
    ws2.column_dimensions[k].width = 14

wb.save(os.path.join(EVAL, "eval_index.xlsx"))
print(f"pack for {len(rows)} papers -> {EVAL}")
print("total model candidates:", sum(r[-1] for r in rows))
