# -*- coding: utf-8 -*-
"""AI expert review of the 28 seed facts against full_v1 predictions.

Verdicts are made by reading the paper context in review_digest.md:
  supported / partial / unsupported / undetermined
  + strict_structured: entity, property, value, unit, conditions, value-category
    (experimental vs simulated) and attribution all aligned in the prediction.
This is a single-pass AI review, NOT independent human gold.
"""
import csv
import json
import os
from collections import Counter

ROOT = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\ai-knowledge-graph-main"
CASES = json.load(open(os.path.join(ROOT, "evaluation", "full_v1", "review_cases.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "evaluation", "full_v1", "ai_review_28.csv")

# fact_id -> (paper_verdict, strict_structured, prediction_form, reason)
V = {
    "01-001": ("partial", "no", "structured",
               "数值来自模拟能带图（simulated），不是测量值；主体粒度也不同（p-NiOx/n-Ga2O3 HJ vs Ga2O3 HJ diode）"),
    "01-002": ("supported", "no", "missing", "原文明确给出 IF on/off 10^9–10^10；模型未抽取"),
    "02-001": ("supported", "no", "raw", "原文为“>20%”的定性上限；模型抽到但数值未结构化（value=None）"),
    "02-002": ("supported", "no", "raw+obs", "23.4% 正确；但观测节点挂在泛化的“PeLEDs”上，主体归属丢失"),
    "02-003": ("partial", "no", "missing", "“<1 ps”属于 GSB build-up time，主体写 energy transfer 是推论；模型未抽取"),
    "03-001": ("supported", "no", "missing", "原文明确 5×10^8 cm^-2；模型未抽取（同篇只抽到 5 V 等噪声）"),
    "03-002": ("partial", "no", "missing", "原文“below 3×10^8”紧接 without-SL 与 SL 对比，归属到 with-SL 需回原文确认；模型未抽取"),
    "04-001": ("supported", "no", "missing", "5.1×10^7 A/W 原文明确；模型未抽取"),
    "04-002": ("supported", "yes", "structured", "2×10^16 Jones 主体、性能、单位一致"),
    "04-003": ("supported", "no", "missing", "32×32 原文明确；模型未抽取（分辨率类数值）"),
    "05-001": ("supported", "no", "raw", "数值正确，但属综述转引（Ong et al.）；模型抽取未结构化且证据匹配失败"),
    "05-002": ("supported", "no", "raw", "1.4 @100 ppm 乙醇正确；模型抽取未结构化"),
    "05-003": ("supported", "no", "missing", "定性依赖原文明确；模型未抽（应由 depends on 覆盖）"),
    "06-001": ("supported", "yes", "structured", "1.75 mS/µm、intrinsic transconductance、主体一致"),
    "06-002": ("supported", "no", "raw", ">1 mA/µm 正确；模型抽取未结构化"),
    "06-003": ("supported", "no", "missing", "定性 XAS 特征；模型未抽取"),
    "07-001": ("supported", "no", "missing", "640×512 原文明确；模型未抽取"),
    "07-002": ("supported", "no", "raw+obs", "17.8 nA cm^-2 正确；结构化观测挂在 NiOx/PbS 器件上，主体不一致，且 -0.5 V 条件丢失"),
    "07-003": ("supported", "no", "missing", "490 ns 上升时间；模型未抽取"),
    "08-001": ("supported", "no", "missing", "10^9 Ω·cm @300 K；模型未抽取"),
    "08-002": ("partial", "no", "missing", "原文把它叫 breakdown voltage，但单位 MV/m 是击穿场强；量纲语义需修正；模型未抽取"),
    "08-003": ("partial", "no", "missing", "1.15×10^-8 F/cm^2 与 SiO2 同值，归属需靠上下文（11.5 / 40 nm）；模型未抽取"),
    "09-001": ("supported", "no", "missing", "4.5×10^-4 S m^-1 原文明确；模型未抽取"),
    "09-002": ("supported", "no", "raw", "“>3.0-fold higher PLQY”正确，属相对倍数；模型抽取未结构化，证据受上下标影响匹配失败"),
    "09-003": ("supported", "no", "missing", "control LED T90=30 min；模型未抽取"),
    "10-001": ("supported", "no", "raw", "up to 2 μm 正确；模型抽取未结构化（value=None）"),
    "10-002": ("supported", "no", "raw", "~80% @1000 h/60°C/20%RH 正确；模型抽取未结构化且条件丢失"),
    "10-003": ("supported", "no", "missing", ">24% after 10 h MPP；模型未抽取"),
}

rows = []
for c in CASES:
    fid = c["fact_id"]
    verdict, strict, form, reason = V[fid]
    g = c["gold"]
    rows.append({
        "fact_id": fid, "paper": c["paper"][:48],
        "gold_subject": g["subject"], "gold_predicate": g["predicate_canonical"],
        "gold_object": g["object"], "gold_property": g["property"],
        "gold_value": g["value"], "gold_unit": g["unit"],
        "paper_verdict": verdict, "strict_structured": strict,
        "prediction_form": form, "review_reason": reason,
        "reviewer": "codex-ai-pass1", "independent_human": "no",
    })

with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

verdicts = Counter(r["paper_verdict"] for r in rows)
strict = Counter(r["strict_structured"] for r in rows)
forms = Counter(r["prediction_form"] for r in rows)
print("paper truth:", dict(verdicts))
print("strict structured:", dict(strict))
print("prediction form:", dict(forms))
print("written", OUT)
