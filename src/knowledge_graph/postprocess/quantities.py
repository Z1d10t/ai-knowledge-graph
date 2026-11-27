# -*- coding: utf-8 -*-
"""Quantity parsing and observation-node construction.

A materials fact like ``CsPbI3 film —has efficiency→ 20.1 %`` is not a plain edge:
the number belongs to a specific sample/device, under specific conditions, measured by
a specific technique. This module turns such edges into explicit observation nodes:

    sample-042      —has measurement→  obs-doi...-003
    obs-doi...-003  —measures→         power conversion efficiency
    obs-doi...-003  —measured by→      J-V
"""
from __future__ import annotations

import re
from typing import Any

# value(s) with optional comparator / uncertainty / unit
_UNIT = (r"%|wt%|at%|eV|meV|cm2\s*[·/]?\s*V-1\s*[·/]?\s*s-1|cm2/Vs|cm2\s*V\s*-1\s*s\s*-1|"
         r"W\s*m\s*\^?-1\s*K\s*\^?-1|W/mK|W\s*m−1\s*K−1|W\s*m-1\s*K-1|"
         r"mA/cm2|mA\s*cm-2|A/W|A\s*W-1|Jones|"
         r"MV/m|MV\s*cm-1|kV/cm|V/cm|V/µm|"
         r"S/m|S\s*m-1|mS/µm|S/cm|"
         r"F/cm2|µF/cm2|uF/cm2|pF|nF|"
         r"Ω\s*[·.]?\s*cm|ohm\s*[·.]?\s*cm|"
         r"V|mV|mA|µA|uA|nm|µm|um|Å|A|h|hr|hrs|hours?|min|minutes?|ms|µs|us|ns|ps|fs|s|sec|"
         r"°C|℃|C|K|°|cm-1|cm−1|W/m2|mW/cm2|sun|cm2|cm-2|mol/L|M|ppm|ppb|a\.u\.|dB|Hz|kHz|MHz|GHz|ohm|Ω|"
         r"nm2|g/cm3|mg/mL|mg|g|µg|ug|mL|L|µL|-?fold|pixels?|px")
_QUALIFIER = r"(?:up\s+to|around|about|over|above|below|nearly|approximately|~|>|<|≥|≤|at\s+least|at\s+most)?\s*"
_QTY = re.compile(
    r"(?P<prefix>" + _QUALIFIER + r")"
    r"(?P<value>[-+]?\d+(?:\.\d+)?(?:\s*[–-]\s*\d+(?:\.\d+)?)?)"
    r"(?P<unc>\s*(?:±|\+/-|\+-)\s*\d+(?:\.\d+)?)?"
    r"(?:\s*(?P<unit>" + _UNIT + r"))?",
    re.IGNORECASE,
)
# "5 × 10^8 cm-2", "1.15×10^-8 F/cm2", "10^9 Ω cm", "below 3 × 10^8 cm^-2"
_SCI = re.compile(r"(?P<q>" + _QUALIFIER + r")(?P<m>\d+(?:\.\d+)?)\s*[×x]\s*10\s*\^?\s*(?P<e>-?\d+)\s*"
                  r"(?P<unit>" + _UNIT + r")?", re.IGNORECASE)
_POW10 = re.compile(r"(?P<q>" + _QUALIFIER + r")10\s*\^?\s*(?P<e>-?\d+)\s*(?P<unit>" + _UNIT + r")?",
                    re.IGNORECASE)
# "around 80% of initial efficiency after 1,000 h" -> value + trailing condition
_VALUE_WITH_CONDITION = re.compile(
    r"(?P<q>" + _QUALIFIER + r")(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>" + _UNIT + r")\s*"
    r"(?:of\s+[^,;]*?)?(?:after|during|for|over)\s+(?P<cond>.{2,40})$", re.IGNORECASE)
# image-array size: 640×512 / 32 × 32
_RES = re.compile(r"(?P<a>\d+)\s*[×x]\s*(?P<b>\d+)\s*(?P<unit>pixels?|px)?", re.IGNORECASE)

MEASUREMENT_PREDICATES = {
    "has efficiency", "has bandgap", "has mobility", "exhibits", "achieves", "retains",
    "has measurement", "degrades after", "operates at", "lasts",
    "has thermal conductivity", "has conductivity", "has carrier lifetime", "has detectivity",
    "has responsivity", "has eqe", "has open-circuit voltage", "has voltage", "has current",
}

PROPERTY_NAMES = {
    "has efficiency": "power conversion efficiency",
    "has bandgap": "bandgap",
    "has mobility": "carrier mobility",
    "retains": "stability retention",
    "degrades after": "degradation",
    "operates at": "operating temperature",
    "lasts": "operational lifetime",
    "has thermal conductivity": "thermal conductivity",
    "has conductivity": "electrical conductivity",
    "has carrier lifetime": "carrier lifetime",
    "has detectivity": "specific detectivity",
    "has responsivity": "responsivity",
    "has eqe": "external quantum efficiency",
    "has open-circuit voltage": "open-circuit voltage",
}

UNIT_CANON = {
    "w m^-1 k^-1": "W m-1 K-1", "w m-1 k-1": "W m-1 K-1", "w m−1 k−1": "W m-1 K-1",
    "w/mk": "W m-1 K-1", "w m -1 k -1": "W m-1 K-1",
    "a w-1": "A W-1", "a/w": "A W-1",
    "cm2 v-1 s-1": "cm2 V-1 s-1", "cm2/vs": "cm2 V-1 s-1",
}


def canon_unit(unit: str | None) -> str | None:
    if not unit:
        return None
    key = re.sub(r"\s+", " ", str(unit).strip().lower())
    return UNIT_CANON.get(key, str(unit).strip())


_UNIT_CARET = re.compile(r"\b(cm|nm|mm|µm|um|m|s|V|A|W|F|g|mol|K)\s*\^\s*(-?)(\d)")


def _normalize_text(s: str) -> str:
    """Unify unit notation before parsing (cm^-2 -> cm-2, ∙ -> ·)."""
    s = s.replace("∙", "·").replace("−", "-").replace("μ", "µ")
    s = _UNIT_CARET.sub(r"\1\2\3", s)
    return re.sub(r"\s+", " ", s).strip()


def _qualifier_to_comparator(q):
    q = (q or "").strip().lower()
    return {"up to": "≤", "above": ">", "over": ">", "below": "<", "at least": "≥",
            "at most": "≤", "around": "~", "about": "~", "approximately": "~",
            "nearly": "~"}.get(q, q or None)


def parse_quantity(text: str) -> dict[str, Any] | None:
    """Parse a short string into a quantity record, or ``None`` when it is not numeric.

    Handles plain values ("20.1%"), qualifiers ("up to 2 μm", "over 10^9 Ω cm"),
    uncertainty ("25.6 ± 0.2%"), ranges ("20.1-21.3%"), scientific notation
    ("5 × 10^8 cm-2"), image resolutions ("640×512") and a value followed by a
    condition ("around 80% of initial efficiency after 1,000 h").
    """
    s = str(text or "").strip()
    if not s or len(s) > 80:
        return None
    s = _normalize_text(s)
    s = re.sub(r"^[A-Za-z][A-Za-z0-9_()/\s]{0,12}\s*=\s*(?=[-+]?\d)", "", s)   # "Eads = -0.85 eV"

    m = _VALUE_WITH_CONDITION.fullmatch(s)
    if m:
        return {"value_raw": s, "value": float(m.group("value")),
                "unit": canon_unit(m.group("unit")) or None,
                "comparator": _qualifier_to_comparator(m.group("q")),
                "uncertainty": None, "notation": "value+condition",
                "conditions": [{"kind": "context", "value": m.group("cond").strip()}]}

    m = _SCI.fullmatch(s)
    if m:
        value = float(m.group("m")) * (10 ** int(m.group("e")))
        unit = (m.group("unit") or "").strip()
        return {"value_raw": s, "value": value, "unit": canon_unit(unit) or None,
                "comparator": _qualifier_to_comparator(m.group("q")), "uncertainty": None,
                "notation": "scientific"}

    m = _POW10.fullmatch(s)
    if m:
        unit = (m.group("unit") or "").strip()
        return {"value_raw": s, "value": float(10 ** int(m.group("e"))), "unit": canon_unit(unit) or None,
                "comparator": _qualifier_to_comparator(m.group("q")), "uncertainty": None,
                "notation": "power"}

    m = _RES.fullmatch(s)
    if m:
        return {"value_raw": s, "value": f"{m.group('a')}x{m.group('b')}", "unit": "pixels",
                "comparator": None, "uncertainty": None, "notation": "resolution"}

    m = _QTY.fullmatch(s)
    if not m:
        return None
    raw_value = m.group("value")
    unit = (m.group("unit") or "").strip()
    comparator = _qualifier_to_comparator(m.group("prefix"))
    uncertainty = (m.group("unc") or "").strip() or None
    record: dict[str, Any] = {"value_raw": s, "unit": canon_unit(unit) or None, "comparator": comparator,
                              "uncertainty": uncertainty}
    if re.search(r"\d\s*[–-]\s*\d", raw_value):
        low, high = re.split(r"\s*[–-]\s*", raw_value, maxsplit=1)
        record.update(value=None, range=[float(low), float(high)])
    else:
        try:
            record["value"] = float(raw_value)
        except ValueError:
            return None
    if unit == "%" and record.get("value") is not None:
        record["normalized_value"] = round(record["value"] / 100.0, 6)
        record["normalized_unit"] = "fraction"
    return record


def _slug(s: str, limit: int = 40) -> str:
    t = re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")
    return t[:limit].rstrip("-") or "x"


def build_observations(triples: list[dict], paper_id: str = "paper") -> tuple[list[dict], int]:
    """Replace numeric property edges by observation nodes.

    Returns ``(new_triples, observation_count)``. Non-numeric edges pass through unchanged.
    """
    out: list[dict] = []
    obs_count = 0
    used_ids: set[str] = set()

    for t in triples:
        if t.get("inferred"):
            out.append(t)
            continue
        predicate = " ".join(str(t.get("predicate") or "").lower().split())
        subject, obj = t.get("subject"), t.get("object")
        qty = parse_quantity(obj)
        looks_like_measurement = predicate in MEASUREMENT_PREDICATES or t.get("object_type") == "measurement"
        if not qty or not looks_like_measurement or not subject:
            out.append(t)
            continue

        obs_count += 1
        obs_id = f"obs-{_slug(paper_id, 28)}-{obs_count:03d}"
        while obs_id in used_ids:
            obs_count += 1
            obs_id = f"obs-{_slug(paper_id, 28)}-{obs_count:03d}"
        used_ids.add(obs_id)

        prop = t.get("property") or PROPERTY_NAMES.get(predicate) or predicate
        shared = {k: t[k] for k in ("source", "chunk", "document", "section", "page", "table_id",
                                    "row_label", "column_header", "evidence_level") if t.get(k)}
        edge = {
            "subject": subject,
            "subject_type": t.get("subject_type"),
            "predicate": "has measurement",
            "object": obs_id,
            "object_type": "measurement",
            "property": prop,
            "value_raw": qty["value_raw"],
            "value": qty.get("value"),
            "unit": qty.get("unit"),
            "conditions": t.get("conditions") or qty.get("conditions"),
            "sample_id": t.get("sample_id"),
            "device_id": t.get("device_id"),
            "raw_predicate": t.get("predicate"),
            "paper_id": t.get("paper_id") or paper_id,
            "extracted": True,
            **shared,
        }
        for k in ("value", "unit", "conditions", "sample_id", "device_id"):
            if edge[k] is None:
                edge.pop(k)
        if qty.get("normalized_value") is not None:
            edge["normalized_value"] = qty["normalized_value"]
            edge["normalized_unit"] = qty.get("normalized_unit")
        if qty.get("range"):
            edge["range"] = qty["range"]
        if qty.get("comparator"):
            edge["comparator"] = qty["comparator"]
        if qty.get("uncertainty"):
            edge["uncertainty"] = qty["uncertainty"]

        out.append(edge)
        out.append({
            "subject": obs_id, "subject_type": "measurement",
            "predicate": "measures", "object": prop, "object_type": "property",
            "paper_id": edge["paper_id"], **shared,
        })
        method = t.get("method") or t.get("characterization")
        if method:
            out.append({
                "subject": obs_id, "subject_type": "measurement",
                "predicate": "measured by", "object": method, "object_type": "characterization",
                "paper_id": edge["paper_id"], **shared,
            })
    return out, obs_count


def count_by_origin(triples: list[dict]) -> dict[str, int]:
    """Split edges into extracted / observation / inferred / ontology counts."""
    counts = {"extracted": 0, "observation": 0, "inferred": 0, "ontology": 0}
    for t in triples:
        if t.get("inferred"):
            counts["ontology" if t.get("method") == "ontology" else "inferred"] += 1
        elif t.get("predicate") in ("has measurement", "measures", "measured by") and \
                (str(t.get("object", "")).startswith("obs-") or str(t.get("subject", "")).startswith("obs-")):
            counts["observation"] += 1
        else:
            counts["extracted"] += 1
    return counts


def predicate_stats(triples: list[dict]) -> dict:
    canonical: set[str] = set()
    unmapped: dict[str, int] = {}
    for t in triples:
        p = str(t.get("predicate") or "")
        if t.get("unmapped"):
            unmapped[p] = unmapped.get(p, 0) + 1
        else:
            canonical.add(p)
    top = sorted(unmapped.items(), key=lambda kv: -kv[1])[:10]
    return {
        "canonical_predicate_types": len(canonical),
        "unmapped_predicate_types": len(unmapped),
        "unmapped_edges": sum(unmapped.values()),
        "unmapped_top": top,
    }


_NUMERIC_HINT = re.compile(r"^\s*(?:up\s+to|around|about|over|above|below|nearly|approximately|~|>|<|≥|≤|"
                           r"at\s+least|at\s+most)?\s*[-+]?\d")


def collect_parse_failures(triples: list[dict]) -> list[dict]:
    """Measurement-looking edges whose numeric object could not be parsed.

    Nothing is dropped: these edges stay in the graph with their verbatim object and
    are listed here so a later parser revision can be re-run over the raw output.
    Only objects that *start* with a number are reported, so chemical formulas
    ("TiO2", "4Cl-BZS") do not show up as false positives.
    """
    failures = []
    for t in triples:
        if t.get("inferred") or str(t.get("object", "")).startswith("obs-"):
            continue
        predicate = " ".join(str(t.get("predicate") or "").lower().split())
        obj = str(t.get("object") or "")
        if not _NUMERIC_HINT.match(obj):
            continue
        if predicate in MEASUREMENT_PREDICATES or t.get("object_type") == "measurement":
            if parse_quantity(obj) is None:
                failures.append({"subject": t.get("subject"), "predicate": t.get("predicate"),
                                 "object": obj, "property": t.get("property"),
                                 "chunk": t.get("chunk"), "source": t.get("source")})
    return failures
