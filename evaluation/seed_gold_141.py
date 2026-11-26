# -*- coding: utf-8 -*-
"""Seed gold annotation for paper 141 (3C-SiC thermal conductivity).

Scope: ABSTRACT + first INTRODUCTION paragraphs (the two paragraphs above).
This is a worked example that validates the harness; it is NOT the full 30-paper gold.
"""
import csv
import os

EVAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evaluation")
GOLD = os.path.join(EVAL, "gold")
os.makedirs(GOLD, exist_ok=True)

FIELDS = ["fact_id", "in_scope", "subject", "subject_type", "predicate_canonical", "predicate_raw",
          "object", "object_type", "property", "value_raw", "value", "unit", "comparator", "uncertainty",
          "sample_or_device", "conditions", "characterization", "evidence_quote", "evidence_location",
          "origin", "merge_error", "unmapped_verdict", "annotator", "notes"]

rows = [
    dict(fact_id="141-01", in_scope="1", subject="3C-SiC crystals", subject_type="material",
         predicate_canonical="has thermal conductivity", predicate_raw="reports thermal conductivity",
         object=">500 W m-1 K-1", object_type="measurement", property="thermal conductivity",
         value_raw=">500 W m-1 K-1", value="500", unit="W m-1 K-1", comparator=">", uncertainty="",
         sample_or_device="wafer-scale cubic silicon carbide (3C-SiC) crystals", conditions="room temperature",
         characterization="", origin="stated", merge_error="", unmapped_verdict="", annotator="AI-seed",
         notes="abstract; isotropic value",
         evidence_quote="We report an isotropic high thermal conductivity over 500 W m-1 K-1 at room temperature in high-quality wafer-scale cubic silicon carbide (3C-SiC) crystals",
         evidence_location="Abstract"),
    dict(fact_id="141-02", in_scope="1", subject="3C-SiC", subject_type="material",
         predicate_canonical="is a", predicate_raw="may constitute",
         object="wide-bandgap semiconductor", object_type="material_class", property="", value_raw="",
         value="", unit="", comparator="", uncertainty="", sample_or_device="", conditions="",
         characterization="", origin="stated", merge_error="", unmapped_verdict="", annotator="AI-seed",
         notes="abstract, hedged ('may constitute')",
         evidence_quote="3C-SiC may constitute an excellent wide-bandgap semiconductor for applications of power electronics",
         evidence_location="Abstract"),
    dict(fact_id="141-03", in_scope="1", subject="3C-SiC thin films", subject_type="sample",
         predicate_canonical="exhibits", predicate_raw="are found to have",
         object="record-high in-plane and cross-plane thermal conductivity", object_type="property",
         property="", value_raw="", value="", unit="", comparator="", uncertainty="",
         sample_or_device="3C-SiC thin films", conditions="", characterization="",
         origin="stated", merge_error="", unmapped_verdict="", annotator="AI-seed",
         notes="qualitative claim, no number",
         evidence_quote="the corresponding 3C-SiC thin films are found to have record-high in-plane and cross-plane thermal conductivity",
         evidence_location="Abstract"),
    dict(fact_id="141-04", in_scope="1", subject="6H-SiC", subject_type="material",
         predicate_canonical="has thermal conductivity", predicate_raw="c-axis k of",
         object="324 W m-1 K-1", object_type="measurement", property="thermal conductivity",
         value_raw="324 W m-1 K-1", value="324", unit="W m-1 K-1", comparator="", uncertainty="",
         sample_or_device="6H-SiC", conditions="room temperature, c-axis", characterization="",
         origin="stated", merge_error="", unmapped_verdict="", annotator="AI-seed",
         notes="literature value quoted in introduction",
         evidence_quote="room-temperature c-axis k of 324 W m-1 K-1 for 6H-SiC",
         evidence_location="Introduction"),
    dict(fact_id="141-05", in_scope="1", subject="4H-SiC", subject_type="material",
         predicate_canonical="has thermal conductivity", predicate_raw="c-axis k of",
         object="348 W m-1 K-1", object_type="measurement", property="thermal conductivity",
         value_raw="348 W m-1 K-1", value="348", unit="W m-1 K-1", comparator="", uncertainty="",
         sample_or_device="4H-SiC", conditions="room temperature, c-axis", characterization="",
         origin="stated", merge_error="", unmapped_verdict="", annotator="AI-seed", notes="literature value",
         evidence_quote="348 W m-1 K-1 for 4H-SiC", evidence_location="Introduction"),
    dict(fact_id="141-06", in_scope="1", subject="AlN", subject_type="material",
         predicate_canonical="has thermal conductivity", predicate_raw="k of",
         object="321 W m-1 K-1", object_type="measurement", property="thermal conductivity",
         value_raw="321 W m-1 K-1", value="321", unit="W m-1 K-1", comparator="", uncertainty="",
         sample_or_device="AlN", conditions="room temperature, c-axis", characterization="",
         origin="stated", merge_error="", unmapped_verdict="", annotator="AI-seed", notes="literature value",
         evidence_quote="321 W m-1 K-1 for AlN", evidence_location="Introduction"),
    dict(fact_id="141-07", in_scope="1", subject="6H-SiC", subject_type="material",
         predicate_canonical="has thermal conductivity", predicate_raw="widely-used high k value",
         object="490 W m-1 K-1", object_type="measurement", property="thermal conductivity",
         value_raw="490 W m-1 K-1", value="490", unit="W m-1 K-1", comparator="", uncertainty="",
         sample_or_device="6H-SiC (Slack 1964, steady-state)", conditions="", characterization="steady-state technique",
         origin="stated", merge_error="", unmapped_verdict="", annotator="AI-seed",
         notes="historical value later corrected",
         evidence_quote="the widely-used high k value (490 W m-1 K-1 ) for 6H-SiC is from Slack's measurements back to 1964",
         evidence_location="Introduction"),
    dict(fact_id="141-08", in_scope="1", subject="6H-SiC", subject_type="material",
         predicate_canonical="has thermal conductivity", predicate_raw="corrected this value to",
         object="~320 W m-1 K-1", object_type="measurement", property="thermal conductivity",
         value_raw="~320 W m-1 K-1", value="320", unit="W m-1 K-1", comparator="~", uncertainty="",
         sample_or_device="6H-SiC (TDTR re-measurement)", conditions="", characterization="TDTR",
         origin="stated", merge_error="", unmapped_verdict="", annotator="AI-seed",
         notes="corrected value; same material as 141-07 but different measurement -> separate fact",
         evidence_quote="corrected this value to ~320 W m-1 K-1 for 6H-SiC",
         evidence_location="Introduction"),
    dict(fact_id="141-09", in_scope="1", subject="3C-SiC", subject_type="material",
         predicate_canonical="used in", predicate_raw="applications of",
         object="power electronics", object_type="device", property="", value_raw="", value="", unit="",
         comparator="", uncertainty="", sample_or_device="", conditions="", characterization="",
         origin="stated", merge_error="", unmapped_verdict="", annotator="AI-seed", notes="application claim",
         evidence_quote="suggest that 3C-SiC may constitute an excellent wide-bandgap semiconductor for applications of power electronics",
         evidence_location="Abstract"),
    dict(fact_id="141-10", in_scope="1", subject="boron doping", subject_type="process",
         predicate_canonical="limits", predicate_raw="creates a factor of 2 decrease in",
         object="thermal conductivity of 3C-SiC", object_type="property", property="thermal conductivity",
         value_raw="0.1%", value="0.1", unit="%", comparator="", uncertainty="",
         sample_or_device="3C-SiC", conditions="0.1% boron", characterization="", origin="stated",
         merge_error="", unmapped_verdict="", annotator="AI-seed",
         notes="defect-phonon scattering effect",
         evidence_quote="0.1% boron creates a factor of 2 decrease in k",
         evidence_location="Introduction"),
]

path = os.path.join(GOLD, "141_Cheng_2022_High-thermal-conductivity-in-wafer-scale-cubic-s.csv")
with open(path, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)
print("wrote", path, len(rows), "rows")
