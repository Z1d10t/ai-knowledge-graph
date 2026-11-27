# -*- coding: utf-8 -*-
"""Condition normalization, evidence backfill, value-type detection and deduplication.

These are deterministic post-processing steps over the extracted triples:
  * normalize condition kinds/values into a small controlled vocabulary
  * when the model omitted conditions, look for them in the evidence sentence only
    (never across the whole paper) and mark the provenance as ``evidence_backfill``
  * classify the value as measured / certified / simulated / calculated / theoretical
  * drop duplicated observations within one paper (same sample, property, value, unit,
    conditions and value type), keeping the first evidence and merging chunk refs
"""
from __future__ import annotations

import re
from typing import Any

CONDITION_KINDS = ("illumination", "spectrum", "area", "temperature", "humidity", "atmosphere",
                   "scan", "bias", "time", "concentration", "other")

_PATTERNS = [
    ("illumination", re.compile(r"\b(\d+(?:\.\d+)?\s*sun[s]?|\d+(?:\.\d+)?\s*mW\s*cm[-−]?2|AM\s*1\.5G|"
                                r"one\s+sun|1\s+sun|simulated\s+sunlight)\b", re.I)),
    ("spectrum", re.compile(r"\b(AM\s*0|AM\s*1\.5G?|standard\s+spectrum)\b", re.I)),
    ("area", re.compile(r"\b(\d+(?:\.\d+)?\s*(?:cm2|cm\^2|cm²|mm2|mm\^2)\s*(?:aperture|active)?)\b", re.I)),
    ("temperature", re.compile(r"\b(-?\d+(?:\.\d+)?\s*°C|\d+\s*K)\b")),
    ("humidity", re.compile(r"\b(\d+(?:\.\d+)?\s*%?\s*(?:relative\s+)?humidity)\b", re.I)),
    ("atmosphere", re.compile(r"\b(N2|N₂|nitrogen|air|ambient|argon|vacuum)\b", re.I)),
    ("scan", re.compile(r"\b(reverse|forward|steady[- ]state|MPP|maximum\s+power\s+point)\b", re.I)),
    ("bias", re.compile(r"\b(-?\d+(?:\.\d+)?\s*V\s*bias|-?\d+(?:\.\d+)?\s*V)\b", re.I)),
    ("time", re.compile(r"\b(\d+(?:,\d{3})*(?:\.\d+)?\s*(?:h|hours?|min|minutes?|s|sec))\b", re.I)),
    ("concentration", re.compile(r"\b(\d+(?:\.\d+)?\s*(?:ppm|ppb|mol%|mM|M|wt%))\b", re.I)),
]

_TYPE_PATTERNS = [
    ("certified", re.compile(r"\bcertif(?:ied|ication)\b|accredited\s+lab", re.I)),
    ("simulated", re.compile(r"\bsimulat(?:ed|ion)s?\b|\bDFT\b|first[- ]principles|molecular\s+dynamics", re.I)),
    ("calculated", re.compile(r"\bcalculat(?:ed|ion)s?\b|\bderived\b|\bestimated\b|\bextracted\b", re.I)),
    ("theoretical", re.compile(r"\btheoretical\b|Shockley[- ]Queisser|\bdetailed\s+balance\b|\bpredicted\b", re.I)),
]

_COMPUTED_PROPERTY = re.compile(r"adsorption energy|formation energy|binding energy|activation energy|"
                                r"energy barrier|density of states|band structure|effective mass|"
                                r"defect formation", re.I)
_ATTRIBUTION = re.compile(r"\[\s*\d+(?:\s*[,-]\s*\d+)*\s*\]|\b[A-Z][a-z]+\s+et\s+al\.?")


def _norm_kind(kind: str) -> str:
    k = str(kind or "").strip().lower()
    return k if k in CONDITION_KINDS or k in ("wavelength", "power", "current") else "other"


def normalize_conditions(conditions: Any) -> list[dict]:
    out = []
    for c in conditions or []:
        if isinstance(c, dict):
            value = str(c.get("value") or "").strip()
            if value:
                out.append({"kind": _norm_kind(c.get("kind")), "value": value})
        elif isinstance(c, str) and c.strip():
            out.append({"kind": "other", "value": c.strip()})
    return out


def backfill_conditions(triples: list[dict]) -> int:
    """Attach conditions found in the evidence sentence when the model gave none."""
    filled = 0
    for t in triples:
        if not str(t.get("object", "")).startswith("obs-"):
            continue
        if t.get("conditions"):
            continue
        text = str(t.get("source") or t.get("evidence_quote") or "")
        if not text:
            continue
        found = []
        for kind, pat in _PATTERNS:
            m = pat.search(text)
            if m:
                value = m.group(1) if m.groups() else m.group(0)
                found.append({"kind": kind, "value": str(value).strip()})
        if found:
            # de-duplicate kinds, keep first match per kind
            seen, conds = set(), []
            for c in found:
                if c["kind"] not in seen:
                    seen.add(c["kind"])
                    conds.append(c)
            t["conditions"] = conds
            t["conditions_source"] = "evidence_backfill"
            t["condition_status"] = "reported"
            filled += 1
    return filled


def annotate_condition_status(triples: list[dict]) -> None:
    for t in triples:
        if not str(t.get("object", "")).startswith("obs-"):
            continue
        if t.get("conditions"):
            t.setdefault("conditions_source", "model")
            t["condition_status"] = "reported"
        else:
            t["condition_status"] = "not_reported"


def detect_value_type(triples: list[dict]) -> None:
    for t in triples:
        if t.get("value_type"):
            continue
        text = " ".join(str(t.get(k) or "") for k in ("source", "evidence_quote", "property", "object", "raw_predicate"))
        if _COMPUTED_PROPERTY.search(str(t.get("property") or "")):
            t["value_type"] = "calculated"
            continue
        for label, pat in _TYPE_PATTERNS:
            if pat.search(text):
                t["value_type"] = label
                break
        else:
            if str(t.get("object", "")).startswith("obs-"):
                t["value_type"] = "measured"


def detect_source_study(triples: list[dict]) -> None:
    """Mark numbers quoted from a cited study (reviews, intros)."""
    for t in triples:
        if t.get("source_study"):
            continue
        text = str(t.get("source") or "")
        m = _ATTRIBUTION.search(text)
        if m:
            t["source_study"] = m.group(0)
            t["attribution"] = "cited"


def dedupe_observations(triples: list[dict]) -> tuple[list[dict], int]:
    """Drop duplicate observation edges inside a paper (same sample/property/value/unit/conditions)."""
    seen: dict[tuple, dict] = {}
    out: list[dict] = []
    removed = 0
    for t in triples:
        if not str(t.get("object", "")).startswith("obs-"):
            out.append(t)
            continue
        conds = t.get("conditions") or []
        key = (str(t.get("paper_id")), str(t.get("sample_id") or t.get("subject")).lower(),
               str(t.get("property")).lower(), str(t.get("value")), str(t.get("unit")),
               tuple(sorted((c.get("kind"), c.get("value")) for c in conds if isinstance(c, dict))),
               str(t.get("value_type")))
        if key in seen:
            first = seen[key]
            for k in ("chunk", "source"):
                if t.get(k) and t[k] != first.get(k):
                    first.setdefault("also_in", []).append({k: t[k]})
            removed += 1
            continue
        seen[key] = t
        out.append(t)
    return out, removed


def postprocess(triples: list[dict]) -> dict:
    """Run the full chain and return counters for the run summary."""
    filled = backfill_conditions(triples)
    detect_value_type(triples)
    detect_source_study(triples)
    annotate_condition_status(triples)
    triples, removed = dedupe_observations(triples)
    return {"conditions_backfilled": filled, "observations_deduplicated": removed,
            "triples_after": len(triples)}
