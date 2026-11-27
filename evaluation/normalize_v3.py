"""Build the normalized v3 graph layers from the frozen v2 extraction output.

Stage B of the review plan. The script

1. freezes the v2 inputs by hashing every raw/enriched file;
2. separates the *concept* layer from paper-scoped *samples/instances* and from *mentions*:
   long attribute phrases, composite mentions and sample instances stop being global nodes;
3. mines paper-scoped abbreviation aliases from parenthetical definitions and links the
   expansion instead of promoting abbreviations globally;
4. classifies every concept with ordered head-noun rules and records conflicts;
5. rebuilds relations with predicate family, causal-direction check, polarity/modality and
   evidence line numbers, merging duplicate edges while keeping every source record;
6. applies the adjudicated repairs from ``stage_a`` (the 250 direction error, compound and
   attribute-phrase splits, composite modifier relations, phase -> parent links);
7. writes a new directory plus a v2-id -> v3-id map. The v2 files are never modified.

Outputs (``evaluation/full_v3_normalized/``): concepts.jsonl, instances.jsonl,
mentions.jsonl, relations.jsonl, relations_raw.jsonl, observations.jsonl, alias_index.json,
id_map.json, type_conflicts.json, fixes_applied.json, stats.json, manifest.json.

Usage::

    python evaluation/normalize_v3.py
    python evaluation/normalize_v3.py --limit 12      # reference papers only (smoke test)
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from knowledge_graph.terminology import (  # noqa: E402
    ConceptRegistry,
    classify_type,
    clean_text,
    compact_key,
    evidence_qualifiers,
    extract_parenthetical_aliases,
    identity_key,
    is_abbreviation,
    is_instance_label,
    label_quality,
    normalize_key,
    relation_direction_check,
    relation_family,
    split_attribute_phrase,
)

V2 = ROOT / "evaluation" / "full_v2" / "kg_output"
OUT = ROOT / "evaluation" / "full_v3_normalized"
TARGETED = ROOT / "evaluation" / "targeted_reextract_v3"
MD = ROOT.parent / "材料论文" / "全部_285篇" / "md"
VERSION = "v3.0"

#: Paper stem -> markdown path. A dict avoids glob mismatches on non-ASCII stems
#: (``201_Jeong_2021_Pseudo-halide-anion-engineering-for-α-FAPbI3-per``).
MD_INDEX: dict[str, Path] = {path.stem: path for path in MD.glob("*.md")}


def md_path_for(paper: str) -> Path:
    """Resolve a paper stem to its markdown file, tolerating unicode normalisation."""
    if paper in MD_INDEX:
        return MD_INDEX[paper]
    stem = paper[:24]
    for candidate, path in MD_INDEX.items():
        if candidate.startswith(stem):
            return path
    raise KeyError(f"no markdown for {paper!r}")

#: Chinese retrieval labels. The plan allows unverified translations only as *suggested*
#: labels, so every entry is marked and none is treated as a synonym proof.
ZH_LABELS: dict[str, str] = {
    "formate": "甲酸根", "atomic layer deposition": "原子层沉积",
    "perovskite": "钙钛矿", "perovskites": "钙钛矿类", "solar cells": "太阳能电池",
    "electron transport layer": "电子传输层", "fill factor": "填充因子",
    "defect": "缺陷", "density functional theory": "密度泛函理论",
    "SiO2": "二氧化硅", "HfO2": "二氧化铪", "ZrO2": "二氧化锆", "Ga2O3": "氧化镓",
    "GaN": "氮化镓", "SiC": "碳化硅", "AgBiS2": "硫银铋矿",
    "quantum well": "量子阱", "quantum-well structure": "量子阱结构",
    "dielectric confinement": "介电限域", "quantum confinement": "量子限域",
    "exciton binding energy": "激子结合能", "energy transfer": "能量转移",
    "photoluminescence quantum yield": "光致发光量子产率",
    "ferroelectric order": "铁电序", "antiferroelectric order": "反铁电序",
    "effective oxide thickness": "等效氧化物厚度", "exfoliation": "剥离",
    "solid solution": "固溶体", "MXenes": "MXene", "graphene": "石墨烯",
    "transition metal dichalcogenides": "过渡金属硫族化合物",
    "cation disorder": "阳离子无序", "absorption coefficient": "吸收系数",
    "valence band maximum": "价带顶", "conduction band minimum": "导带底",
    "wide-bandgap perovskites": "宽带隙钙钛矿", "tandem solar cells": "叠层太阳能电池",
    "open-circuit voltage deficit": "开路电压亏损", "thermalization losses": "热弛豫损失",
    "charge transport layers": "电荷传输层", "hole-selective contact": "空穴选择接触",
    "self-assembled monolayer": "自组装单分子层", "indium tin oxide": "氧化铟锡",
    "specific on-resistance": "比导通电阻", "breakdown voltage": "击穿电压",
    "operating temperature": "工作温度", "grain boundaries": "晶界",
    "anion-vacancy defects": "阴离子空位缺陷", "crystallinity": "结晶性",
    "alpha-FAPbI3": "α相甲脒铅碘", "delta-FAPbI3": "δ相甲脒铅碘",
    "formamidinium lead triiodide": "甲脒铅碘", "colloidal nanocrystals": "胶体纳米晶",
    "cation segregation": "阳离子偏析", "inorganic molecular crystal": "无机分子晶体",
    "van der Waals dielectrics": "范德华介电材料", "electron mobility": "电子迁移率",
    "epitaxy": "外延", "p-type doping": "p型掺杂",
}

#: Adjudicated repairs applied by (paper, v2 edge index). Every application is recorded.
FIXES = [
    {
        "fix_id": "fx-250-direction",
        "kind": "reverse_relation",
        "paper": "250_Wang_2022_Cation-disorder-engineering-yields-AgBiS2-nanocr",
        "v2_index": 157,
        "before": {"subject": "absorption coefficients of ternary AgBiS2 NCs", "predicate": "improves",
                   "object": "cation disorder homogenization under mild annealing conditions"},
        "after": {"subject": "cation disorder homogenization under mild annealing conditions",
                  "predicate": "improves",
                  "object": "absorption coefficients of ternary AgBiS2 NCs"},
        "reason": "a quantity cannot cause a process; the paper states the process enhances absorption",
    },
]

#: Phase-specific materials linked to the parent formula (adjudicated, evidenced by the paper).
PHASE_PARENTS = {
    "alpha-FAPbI3": "formamidinium lead triiodide",
    "delta-FAPbI3": "formamidinium lead triiodide",
    "α-FAPbI3": "formamidinium lead triiodide",
    "δ-FAPbI3": "formamidinium lead triiodide",
}

#: Labels that are surface forms of a cleaner concept; the value is the canonical name.
KNOWN_SYNONYMS = {
    "HCOO−": "formate", "HCOO-": "formate",
    "vdW dielectric": "van der Waals dielectrics",
    "vdW dielectrics": "van der Waals dielectrics",
    "two-dimensional transition metal dichalcogenides materials": "transition metal dichalcogenides",
    "WBG perovskites": "wide-bandgap perovskites",
    "VOC deficit": "open-circuit voltage deficit",
    "CBM": "conduction band minimum", "VBM": "valence band maximum",
    "FPAs": "focal plane arrays",  # 023 defines it in the abstract; used as a curated alias
    "APDs": "avalanche photodiodes",
    "V_OC deficit": "open-circuit voltage deficit",
    "Ron,sp": "specific on-resistance",
    "perovskite LEDs": "perovskite light-emitting diodes",
    # Appositive ligand abbreviations: the paper writes "4- chlorobenzenesulfonate, 4Cl-BZS"
    # without parentheses, so the parenthetical miner cannot see them.
    "4Cl-BZS": "4-chlorobenzenesulfonate",
    "4- chlorobenzenesulfonate": "4-chlorobenzenesulfonate",
    "4CH3-BZS": "4-methylbenzenesulfonate",
    "BZS": "benzenesulfonate",
    # Ionic forms of a named species
    "HCOO- anion": "formate", "HCOO- anions": "formate", "HCOO− anions": "formate",
    "HCOO- anion": "formate", "formate anions": "formate", "formate anion": "formate",
    # Element-name spellings of formulas (the reference aliases and the model both use them)
    "antimony trioxide": "Sb2O3",
    "gallium oxide": "Ga2O3",
    "gallium nitride": "GaN",
    "silicon carbide": "SiC",
    "ITO": "indium tin oxide",
    "hafnium oxide": "HfO2",
    "zirconium oxide": "ZrO2",
    "silicon dioxide": "SiO2",
}

_SYNONYM_BY_KEY = {compact_key(key): value for key, value in KNOWN_SYNONYMS.items()}


def canonical_synonym(label: str) -> str:
    """Case-insensitive known-synonym lookup (surface form -> canonical concept name)."""
    return _SYNONYM_BY_KEY.get(compact_key(label), label)

#: Compound labels the review found merged (Stage A split_compound actions). Each component
#: becomes its own concept, the compound stays a concept and is linked via "composed of".
_COMPOUND_LABELS = {
    "carbides, carbonitrides, and nitrides": ["carbides", "nitrides", "carbonitrides"],
    "quantum- and dielectric-confinement effects": ["quantum confinement", "dielectric confinement"],
    "charge transport layers and buffer layers": ["charge transport layers", "buffer layers"],
    "mixed ferroelectric-antiferroelectric order": ["ferroelectric order", "antiferroelectric order"],
    "VBM and CBM delocalized over the entire material": ["VBM", "CBM"],
}
COMPOUND_SPLITS: dict[str, list[str]] = {compact_key(key): value for key, value in _COMPOUND_LABELS.items()}


class LineIndex:
    """Map an evidence quote back to the markdown line it came from."""

    def __init__(self, text: str) -> None:
        self.lines = text.splitlines()
        self.clean = [clean_text(line) for line in self.lines]
        self.blob = "\n".join(self.clean)
        self.offsets, position = [], 0
        for line in self.clean:
            self.offsets.append(position)
            position += len(line) + 1
        self.low = self.blob.lower()

    def locate(self, quote: str) -> int | None:
        needle = clean_text(quote or "").strip()[:90].lower()
        if len(needle) < 8:
            return None
        position = self.low.find(needle)
        if position < 0:
            needle = needle[:50]
            position = self.low.find(needle) if len(needle) >= 8 else -1
            if position < 0:
                return None
        return bisect.bisect_right(self.offsets, position)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


#: Unit tokens accepted after a number. Anything else means the label is a phrase, not a
#: value ("2D material" must not be read as the number 2 with unit "D material").
_UNITS = frozenset({
    "%", "‰", "cm", "cm2", "cm-2", "cm-3", "m", "mm", "nm", "µm", "μm", "å", "a", "k", "°c",
    "ev", "v", "kv", "mv", "w", "mw", "gw", "kw", "s", "ms", "ns", "µs", "us", "h", "min",
    "hz", "khz", "mhz", "ghz", "ma", "ua", "µa", "mol", "mm2", "g", "mg", "kg", "l", "ml",
    "wt%", "at%", "ppm", "ppb", "torr", "pa", "kpa", "mpa", "gpa", "ohm", "ω", "deg",
    "°", "rpm", "sccm", "times", "x", "fold", "um", "µm2", "mev", "kev", "wh", "kwh",
    "j", "kj", "mj", "µj", "nf", "pf", "µf", "f", "db", "cm3", "mm3", "µl",
})


def is_value_label(label: str, label_type: str) -> bool:
    """Numeric measurement values are facts, not concepts.

    ``20.1%``, ``8.32 kV`` and ``65 °C`` are values; ``2D material`` and ``10 µm film`` are
    not, even though they start with a digit.
    """
    if label_type in {"measurement"}:
        return True
    value = clean_text(label).strip()
    if not value:
        return True
    value = re.sub(r"^[<>~∼≈≥≤]\s*", "", value).replace("−", "-")
    tokens = value.split()
    if not tokens:
        return True
    match = re.match(r"^-?\d+(?:\.\d+)?", tokens[0])
    if not match:
        return False
    rest = tokens[0][match.end():].strip()
    if rest and rest.lower() not in _UNITS:
        return False
    for token in tokens[1:]:
        if token.lower().strip(".,;") not in _UNITS:
            return False
    return True


def compound_components(label: str) -> list[str]:
    """Components of a known compound label (exact compact-key match only)."""
    return COMPOUND_SPLITS.get(compact_key(label), [])


def build(papers: list[str], limit: int | None = None) -> dict:
    registry = ConceptRegistry()
    mentions: list[dict] = []
    instances: list[dict] = []
    relations: list[dict] = []
    observations: list[dict] = []
    numeric_facts: list[dict] = []
    raw_relations: list[dict] = []
    fixes_applied: list[dict] = []
    term_log: list[dict] = []
    label_map: dict[str, dict[str, str]] = defaultdict(dict)
    counters: Counter = Counter()

    for paper_number, paper in enumerate(papers, start=1):
        if limit and paper_number > limit:
            break
        enriched_path = V2 / "enriched" / f"{paper}.json"
        triples = json.loads(enriched_path.read_text(encoding="utf-8"))
        md_path = md_path_for(paper)
        md_text = md_path.read_text(encoding="utf-8")
        line_index = LineIndex(md_text)
        alias_hits = extract_parenthetical_aliases(md_text)
        expansions = {hit["alias"]: hit["expansion"] for hit in alias_hits}
        counters["paper_aliases_mined"] += len(alias_hits)
        paper_fixes = {fix["v2_index"]: fix for fix in FIXES if fix["paper"] == paper}
        locate_cache: dict[str, int | None] = {}

        def locate(evidence: str) -> int | None:
            """Cached evidence -> line lookup (the same sentence often supports several facts)."""
            key = evidence[:200]
            if key not in locate_cache:
                locate_cache[key] = line_index.locate(evidence)
            return locate_cache[key]

        def resolve(label: str, label_type: str, evidence: str) -> dict:
            """Label -> concept (or paper-scoped instance / value / symbol)."""
            original = clean_text(label)
            if not original:
                return {}
            if original.startswith("obs-"):
                return {"kind": "observation"}
            if is_value_label(original, label_type):
                counters["value_mentions"] += 1
                return {"kind": "value", "surface": original}
            quality = label_quality(original)
            if quality == "symbol":
                counters["symbol_fragments"] += 1
                return {"kind": "symbol", "surface": original}

            split = split_attribute_phrase(original)
            head = split.head or original
            surface = original

            # A label that already carries its abbreviation in parentheses
            # ("focal plane arrays (FPAs)", "standard thermal evaporation deposition (STED)")
            # is the expansion plus an alias, not a concept with a bracket in its name.
            embedded = re.match(r"^(?P<name>[^()]{3,80}?)\s*\((?P<abbr>[^()]{1,20})\)\s*$", original)
            if embedded and is_abbreviation(embedded.group("abbr")):
                base = canonical_synonym(embedded.group("name").strip())
                record = registry.add(paper, base, [label_type],
                                      alias=embedded.group("abbr").strip(), evidence=evidence)
                counters["embedded_alias_split"] += 1
                return {"kind": "concept", "concept": record, "surface": surface,
                        "attributes": split.as_dict()}

            if is_instance_label(original):
                instance_id = "i-" + hashlib.sha1(f"{paper}|{original}".encode("utf-8")).hexdigest()[:12]
                if not any(item["instance_id"] == instance_id for item in instances):
                    instances.append({
                        "instance_id": instance_id,
                        "paper_id": paper,
                        "label": original,
                        "type": "sample",
                        "linked_concept_id": None,
                        "evidence": evidence[:300],
                    })
                counters["instance_mentions"] += 1
                return {"kind": "instance", "id": instance_id, "surface": surface,
                        "concept_type": "sample"}

            if split.kind == "composite":
                modifier = split.modifiers[0] if split.modifiers else ""
                target = registry.add(paper, head, [label_type],
                                      expansion=_expansion(head, expansions, original),
                                      evidence=evidence)
                composite = registry.add(paper, original, [label_type],
                                         expansion=_expansion(original, expansions, None),
                                         review_status="composite")
                if modifier:
                    modifier_name = canonical_synonym(modifier)
                    modifier_record = registry.add(paper, modifier_name, ["material_class"],
                                                   expansion=_expansion(modifier_name, expansions, None))
                    if modifier_record.concept_id != target.concept_id:
                        relations.append({
                            "subject_id": modifier_record.concept_id,
                            "object_id": target.concept_id,
                            "subject_kind": "concept",
                            "object_kind": "concept",
                            "subject_label": modifier_record.canonical_name,
                            "object_label": target.canonical_name,
                            "subject_type": modifier_record.type,
                            "object_type": target.type,
                            "predicate": "modifies",
                            "raw_predicate": "modifies",
                            "family": "effect",
                            "paper_id": paper,
                            "chunk": 0,
                            "evidence": evidence[:300],
                            "evidence_line": locate(evidence),
                            "polarity": "positive",
                            "modality": "asserted",
                            "direction_ok": True,
                            "direction_issue": "",
                            "scope": "paper_local",
                            "source": "adjudicated_mention_split",
                            "review_status": "adjudicated",
                            "v2_index": None,
                            "composite_label": original,
                        })
                        counters["composite_relations_added"] += 1
                return {"kind": "concept", "concept": target, "surface": surface,
                        "attributes": split.as_dict()}

            canonical_label = canonical_synonym(head)
            expansion = _expansion(canonical_label, expansions, original)
            record = registry.add(paper, canonical_label, [label_type], expansion=expansion,
                                  alias=head if canonical_label != head else None,
                                  evidence=evidence)
            if expansion:
                counters["alias_verified"] += 1

            components = compound_components(original)
            for component in components:
                component = canonical_synonym(component)
                component_record = registry.add(paper, component, [label_type],
                                                expansion=_expansion(component, expansions, None))
                if component_record.concept_id != record.concept_id:
                    relations.append({
                        "subject_id": record.concept_id,
                        "object_id": component_record.concept_id,
                        "subject_kind": "concept",
                        "object_kind": "concept",
                        "subject_label": record.canonical_name,
                        "object_label": component_record.canonical_name,
                        "subject_type": record.type,
                        "object_type": component_record.type,
                        "predicate": "composed of",
                        "raw_predicate": "composed of",
                        "family": "composition",
                        "paper_id": paper,
                        "chunk": 0,
                        "evidence": evidence[:300],
                        "evidence_line": locate(evidence),
                        "polarity": "positive",
                        "modality": "asserted",
                        "direction_ok": True,
                        "direction_issue": "",
                        "scope": "paper_local",
                        "source": "adjudicated_compound_split",
                        "review_status": "adjudicated",
                        "v2_index": None,
                    })
                    fixes_applied.append({
                        "fix_id": "fx-split-" + hashlib.sha1(f"{paper}|{original}|{component}".encode()).hexdigest()[:10],
                        "kind": "split_compound",
                        "paper_id": paper,
                        "before": {"node": original},
                        "after": {"subject": record.canonical_name, "predicate": "composed of",
                                  "object": component_record.canonical_name},
                        "reason": "compound label split into the concepts the review requires",
                        "evidence": evidence[:300],
                        "evidence_line": locate(evidence),
                    })
                    counters["compound_splits"] += 1
            return {"kind": "concept", "concept": record, "surface": surface,
                    "attributes": split.as_dict()}

        # v2 keeps the measured value on the owner edge, so index those first
        owner_by_obs: dict[str, dict] = {}
        for candidate in triples:
            obj = str(candidate.get("object", ""))
            if obj.startswith("obs-") and not str(candidate.get("subject", "")).startswith("obs-"):
                owner_by_obs[obj] = candidate

        for position, triple in enumerate(triples):
            subject_label = str(triple.get("subject", ""))
            object_label = str(triple.get("object", ""))
            evidence = str(triple.get("source") or triple.get("evidence_quote") or "")
            chunk = triple.get("chunk")
            subject_type = str(triple.get("subject_type", ""))
            object_type = str(triple.get("object_type", ""))

            if subject_label.startswith("obs-"):
                # v2 stores value/unit/sample/conditions on the owner edge
                # ("material -> has measurement -> obs-id"), not on the property edge.
                owner = owner_by_obs.get(subject_label, {})

                def first_nonempty(*values):
                    for value in values:
                        if value not in (None, "", [], {}):
                            return value
                    return None

                value = first_nonempty(triple.get("value"), owner.get("value"))
                conditions = first_nonempty(triple.get("conditions"), owner.get("conditions"))
                condition_pairs = len(conditions) if isinstance(conditions, list) else (1 if conditions else 0)
                owner_label = str(owner.get("subject") or "")
                owner_concept = None
                if owner_label and not owner_label.startswith("obs-"):
                    candidate = registry.find_label(owner_label, paper_id=paper)
                    if candidate is None:
                        candidate = registry.find_label(owner_label)
                    owner_concept = candidate.concept_id if candidate else None
                property_record = registry.add(paper, object_label or "", [object_type])
                observations.append({
                    "observation_id": subject_label,
                    "paper_id": paper,
                    "property_concept_id": property_record.concept_id,
                    "property": object_label,
                    "value": value,
                    "value_raw": first_nonempty(triple.get("value_raw"), owner.get("value_raw")),
                    "unit": first_nonempty(triple.get("unit"), owner.get("unit")),
                    "comparator": first_nonempty(triple.get("comparator"), owner.get("comparator")),
                    "range": first_nonempty(triple.get("range"), owner.get("range")),
                    "uncertainty": first_nonempty(triple.get("uncertainty"), owner.get("uncertainty")),
                    "value_type": first_nonempty(triple.get("value_type"), owner.get("value_type")),
                    "conditions": conditions,
                    "condition_status": first_nonempty(triple.get("condition_status"),
                                                        owner.get("condition_status")),
                    "sample_id": first_nonempty(triple.get("sample_id"), owner.get("sample_id")),
                    "source_study": first_nonempty(triple.get("source_study"), owner.get("source_study")),
                    "owner_label": owner_label or None,
                    "owner_type": owner.get("subject_type"),
                    "owner_concept_id": owner_concept,
                    "evidence": evidence[:300],
                    "evidence_owner": str(owner.get("source") or owner.get("evidence_quote") or "")[:300],
                    "evidence_line": locate(evidence) or locate(str(owner.get("source") or "")),
                    "chunk": chunk,
                    "v2_index": position,
                })
                counters["observations"] += 1
                if value not in (None, ""):
                    counters["observations_with_value"] += 1
                if first_nonempty(triple.get("unit"), owner.get("unit")) not in (None, ""):
                    counters["observations_with_unit"] += 1
                if first_nonempty(triple.get("sample_id"), owner.get("sample_id")) not in (None, ""):
                    counters["observations_with_sample"] += 1
                if conditions:
                    counters["observations_with_conditions"] += 1
                    counters["observation_condition_pairs"] += condition_pairs
                if not owner:
                    counters["observations_unmatched"] += 1
                continue

            subject = resolve(subject_label, subject_type, evidence)
            obj = resolve(object_label, object_type, evidence)
            for side, resolved, raw_label in (("subject", subject, subject_label),
                                              ("object", obj, object_label)):
                if not resolved:
                    continue
                mention = {
                    "paper_id": paper,
                    "v2_index": position,
                    "role": side,
                    "surface": resolved.get("surface") or clean_text(raw_label),
                    "mention_kind": resolved.get("kind"),
                    "chunk": chunk,
                    "evidence": evidence[:300],
                    "evidence_line": locate(evidence),
                }
                if resolved.get("concept"):
                    record = resolved["concept"]
                    mention["concept_id"] = record.concept_id
                    mention["concept_name"] = record.canonical_name
                    mention["concept_type"] = record.type
                    label_map[paper][mention["surface"]] = record.concept_id
                if resolved.get("id"):
                    mention["instance_id"] = resolved["id"]
                    label_map[paper][mention["surface"]] = resolved["id"]
                if resolved.get("attributes"):
                    mention["attributes"] = resolved["attributes"]
                mentions.append(mention)
                counters["mentions"] += 1

            subject_kind = subject.get("kind")
            object_kind = obj.get("kind")
            if subject_kind not in {"concept", "instance"} or object_kind not in {"concept", "instance"}:
                # A numeric value on the object side is not a concept, but the claim is kept
                # as an auxiliary numeric fact: v2 numbers stay as extra information.
                if subject_kind in {"concept", "instance"} and object_kind == "value":
                    numeric_facts.append({
                        "paper_id": paper,
                        "subject": (subject["concept"].canonical_name if subject_kind == "concept"
                                    else subject.get("surface")),
                        "subject_id": (subject["concept"].concept_id if subject_kind == "concept"
                                       else subject.get("id")),
                        "predicate": str(triple.get("predicate", "")),
                        "value": object_label,
                        "value_type": triple.get("value_type"),
                        "unit": triple.get("unit"),
                        "property": triple.get("property"),
                        "sample_id": triple.get("sample_id"),
                        "conditions": triple.get("conditions"),
                        "evidence": evidence[:300],
                        "evidence_line": locate(evidence),
                        "chunk": chunk,
                        "v2_index": position,
                    })
                counters["relations_skipped_nonconcept"] += 1
                continue
            subject_id = subject["concept"].concept_id if subject_kind == "concept" else subject["id"]
            object_id = obj["concept"].concept_id if object_kind == "concept" else obj["id"]
            subject_cname = (subject["concept"].canonical_name if subject_kind == "concept"
                             else subject["surface"])
            object_cname = (obj["concept"].canonical_name if object_kind == "concept"
                            else obj["surface"])
            subject_ctype = subject["concept"].type if subject_kind == "concept" else "sample"
            object_ctype = obj["concept"].type if object_kind == "concept" else "sample"

            fix = paper_fixes.get(position)
            predicate = str(triple.get("predicate", "")).strip()
            if fix:
                predicate = fix["after"]["predicate"]
                subject_record = registry.add(paper, fix["after"]["subject"], [subject_type])
                object_record = registry.add(paper, fix["after"]["object"], [object_type])
                subject_id, object_id = subject_record.concept_id, object_record.concept_id
                subject_cname, object_cname = subject_record.canonical_name, object_record.canonical_name
                subject_ctype, object_ctype = subject_record.type, object_record.type
                subject_kind = object_kind = "concept"
                fixes_applied.append({
                    "fix_id": fix["fix_id"], "kind": fix["kind"], "paper_id": paper,
                    "v2_index": position, "before": fix["before"], "after": fix["after"],
                    "evidence": evidence[:300], "evidence_line": locate(evidence),
                    "reason": fix["reason"],
                })

            polarity, modality = evidence_qualifiers(evidence)
            direction = relation_direction_check(subject_ctype, predicate, object_ctype)
            relations.append({
                "paper_id": paper,
                "chunk": chunk,
                "subject_id": subject_id,
                "object_id": object_id,
                "subject_kind": subject_kind,
                "object_kind": object_kind,
                "subject_label": subject_cname,
                "object_label": object_cname,
                "subject_type": subject_ctype,
                "object_type": object_ctype,
                "predicate": predicate,
                "raw_predicate": str(triple.get("predicate", "")),
                "family": relation_family(predicate),
                "evidence": evidence[:300],
                "evidence_line": locate(evidence),
                "evidence_level": triple.get("evidence_level"),
                "evidence_text_match": triple.get("evidence_text_match"),
                "polarity": polarity,
                "modality": modality,
                "direction_ok": direction.ok,
                "direction_issue": direction.issue,
                "scope": "paper_local",
                "source": "adjudicated_fix" if fix else "v2_enriched",
                "review_status": "adjudicated" if fix else "machine",
                "v2_index": position,
            })
            raw_relations.append({**triple, "v2_index": position, "paper_id": paper})
            counters["relations_extracted"] += 1
        counters["papers"] += 1

    # Targeted re-extraction output (Stage C) is fused as additional evidence.
    for path in sorted(TARGETED.glob("*.json")) if TARGETED.exists() else []:
        paper = path.stem
        if not paper[:3].isdigit():
            continue
        if limit and paper not in papers[:limit]:
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        md_path = md_path_for(paper)
        md_text = md_path.read_text(encoding="utf-8")
        line_index = LineIndex(md_text)
        normalized_md = clean_text(md_text).lower()

        # Terms from the targeted run: concepts that may have no relation of their own.
        for term in payload.get("terms", []):
            name = str(term.get("name") or "").strip()
            aliases = [str(alias).strip() for alias in (term.get("aliases") or []) if str(alias).strip()]
            entry = {"paper_id": paper, "name": name, "type": term.get("type"),
                     "aliases": aliases, "status": "", "reason": "", "concept_id": None,
                     "evidence": str(term.get("evidence") or "")[:300], "evidence_line": None}
            if not name:
                entry.update(status="rejected", reason="empty name")
                counters["terms_rejected"] += 1
                term_log.append(entry)
                continue
            if label_quality(name) == "symbol":
                entry.update(status="rejected", reason="symbol fragment")
                counters["terms_rejected"] += 1
                term_log.append(entry)
                continue
            if is_instance_label(name):
                entry.update(status="rejected", reason="paper-local instance label")
                counters["terms_rejected"] += 1
                term_log.append(entry)
                continue
            forms = [name] + aliases
            if not any(len(clean_text(form)) >= 3 and clean_text(form).lower() in normalized_md
                       for form in forms):
                entry.update(status="rejected", reason="term does not occur in the paper text")
                counters["terms_rejected"] += 1
                term_log.append(entry)
                continue
            head = split_attribute_phrase(name).head or name
            canonical = canonical_synonym(head)
            existed = registry.find_label(canonical) is not None
            record = registry.add(paper, canonical, [str(term.get("type") or "")],
                                  review_status="targeted_reextract")
            accepted_aliases = []
            for alias in aliases:
                if compact_key(alias) == compact_key(canonical):
                    continue
                if clean_text(alias).lower() not in normalized_md:
                    continue
                registry.add(paper, alias, [str(term.get("type") or "")], expansion=canonical)
                accepted_aliases.append(alias)
            evidence = entry["evidence"]
            line = line_index.locate(evidence) if evidence else None
            entry.update(status="merged" if existed else "accepted",
                         concept_id=record.concept_id, evidence_line=line,
                         canonical=record.canonical_name, accepted_aliases=accepted_aliases)
            counters["terms_merged" if existed else "terms_accepted"] += 1
            term_log.append(entry)
            mentions.append({
                "paper_id": paper,
                "v2_index": None,
                "role": "term",
                "surface": name,
                "mention_kind": "concept",
                "concept_id": record.concept_id,
                "concept_name": record.canonical_name,
                "concept_type": record.type,
                "chunk": 0,
                "evidence": evidence,
                "evidence_line": line,
                "extractor": "targeted_terms",
            })
            counters["mentions"] += 1

        for item in payload.get("triples", []):
            subject_label = str(item.get("subject", ""))
            object_label = str(item.get("object", ""))
            evidence = str(item.get("evidence", ""))
            if not subject_label or not object_label:
                continue
            if item.get("evidence_text_match") is False:
                counters["targeted_relations_unverified"] += 1
                continue
            # Apply the same concept normalisation as the v2 path: the model may emit
            # "SiC film" or a synonym that already has a concept.
            subject_label = canonical_synonym(
                split_attribute_phrase(clean_text(subject_label)).head or subject_label)
            object_label = canonical_synonym(
                split_attribute_phrase(clean_text(object_label)).head or object_label)
            subject_record = registry.add(paper, subject_label, [str(item.get("subject_type", ""))],
                                          review_status="targeted_reextract")
            object_record = registry.add(paper, object_label, [str(item.get("object_type", ""))],
                                         review_status="targeted_reextract")
            polarity, modality = evidence_qualifiers(evidence)
            direction = relation_direction_check(subject_record.type, str(item.get("predicate", "")),
                                                 object_record.type)
            relations.append({
                "paper_id": paper,
                "chunk": item.get("chunk", 0),
                "subject_id": subject_record.concept_id,
                "object_id": object_record.concept_id,
                "subject_kind": "concept",
                "object_kind": "concept",
                "subject_label": subject_record.canonical_name,
                "object_label": object_record.canonical_name,
                "subject_type": subject_record.type,
                "object_type": object_record.type,
                "predicate": str(item.get("predicate", "")),
                "raw_predicate": str(item.get("predicate", "")),
                "family": relation_family(str(item.get("predicate", ""))),
                "evidence": evidence[:300],
                "evidence_line": item.get("evidence_line") or line_index.locate(evidence),
                "evidence_level": item.get("evidence_level", "stated"),
                "evidence_text_match": item.get("evidence_text_match"),
                "polarity": polarity,
                "modality": modality,
                "direction_ok": direction.ok,
                "direction_issue": direction.issue,
                "scope": "paper_local",
                "source": "targeted_reextract",
                "review_status": "adjudicated",
                "v2_index": None,
            })
            counters["targeted_relations"] += 1

    # Phase -> parent links (adjudicated), after all papers are loaded.
    for concept in list(registry.concepts):
        parent_name = PHASE_PARENTS.get(concept.canonical_name)
        if not parent_name:
            continue
        parent = registry.find_label(parent_name)
        if parent is None:
            continue
        relations.append({
            "paper_id": sorted(concept.papers)[0],
            "chunk": 0,
            "subject_id": concept.concept_id,
            "object_id": parent.concept_id,
            "subject_kind": "concept",
            "object_kind": "concept",
            "subject_label": concept.canonical_name,
            "object_label": parent.canonical_name,
            "subject_type": concept.type,
            "object_type": parent.type,
            "predicate": "is a",
            "raw_predicate": "is a",
            "family": "taxonomy",
            "evidence": f"{concept.canonical_name} is a phase of {parent.canonical_name}",
            "evidence_line": None,
            "polarity": "positive",
            "modality": "asserted",
            "direction_ok": True,
            "direction_issue": "",
            "scope": "paper_local",
            "source": "adjudicated_phase_link",
            "review_status": "adjudicated",
            "v2_index": None,
        })
        fixes_applied.append({
            "fix_id": f"fx-phase-{concept.concept_id}",
            "kind": "phase_parent_link",
            "paper_id": sorted(concept.papers)[0],
            "before": None,
            "after": {"subject": concept.canonical_name, "predicate": "is a",
                      "object": parent.canonical_name},
            "reason": "phase-specific materials stay separate concepts and are linked to the parent formula",
            "evidence_line": None,
        })

    # Link samples to the concept they are a sample of (paper-scoped, never merged).
    for instance in instances:
        words = instance["label"].split()
        for size in range(len(words), 0, -1):
            candidate = " ".join(words[:size])
            record = registry.find_label(candidate, paper_id=instance["paper_id"])
            if record is None:
                record = registry.find_label(candidate)
            if record is not None:
                instance["linked_concept_id"] = record.concept_id
                break

    return {"registry": registry, "mentions": mentions, "instances": instances,
            "relations": relations, "observations": observations, "numeric_facts": numeric_facts,
            "raw_relations": raw_relations, "fixes": fixes_applied, "term_log": term_log,
            "label_map": label_map, "counters": counters}


def _expansion(label: str, expansions: dict[str, str], original: str | None) -> str | None:
    """Paper-defined expansion for an abbreviation, if the paper defines one.

    Only real abbreviations get an expansion: a full label such as ``AlGaN`` (a chemical
    formula) must never be re-named after a parenthetical that happens to follow it, and a
    mined expansion that is a clause is rejected by the miner.
    """
    for candidate in (label, original):
        if not candidate or not is_abbreviation(candidate):
            continue
        expansion = expansions.get(candidate)
        if expansion and compact_key(expansion) != compact_key(candidate):
            return expansion
    return None


def deduplicate_relations(relations: list[dict]) -> tuple[list[dict], int]:
    """Merge duplicate edges per paper, keeping every evidence record."""
    grouped: dict[tuple, dict] = {}
    merged = 0
    for relation in relations:
        key = (relation["paper_id"], relation["subject_id"], relation["predicate"],
               relation["object_id"], relation["polarity"])
        if key not in grouped:
            grouped[key] = {
                **relation,
                "relation_id": "r-" + hashlib.sha1(repr(key).encode("utf-8")).hexdigest()[:12],
                "evidence_all": [{"evidence": relation["evidence"],
                                  "evidence_line": relation["evidence_line"],
                                  "chunk": relation["chunk"],
                                  "v2_index": relation["v2_index"]}],
                "v2_indices": [relation["v2_index"]] if relation["v2_index"] is not None else [],
                "duplicate_count": 1,
            }
        else:
            merged += 1
            group = grouped[key]
            group["evidence_all"].append({"evidence": relation["evidence"],
                                          "evidence_line": relation["evidence_line"],
                                          "chunk": relation["chunk"],
                                          "v2_index": relation["v2_index"]})
            if relation["v2_index"] is not None:
                group["v2_indices"].append(relation["v2_index"])
            group["duplicate_count"] += 1
            if relation["review_status"] == "adjudicated":
                group["review_status"] = "adjudicated"
    return list(grouped.values()), merged


def apply_language_labels(registry: ConceptRegistry) -> int:
    """Attach Chinese *suggested* labels; the table is a retrieval hint, not a synonym proof."""
    identity_to_zh = {identity_key(name, classify_type(name)[0]): zh
                      for name, zh in ZH_LABELS.items()}
    applied = 0
    for concept in registry.concepts:
        zh = identity_to_zh.get(concept.identity)
        if zh:
            concept.language_labels = {"en": concept.canonical_name, "zh_suggested": zh}
            applied += 1
    return applied


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize v2 output into the v3 layers")
    parser.add_argument("--limit", type=int, default=0, help="Only the first N papers (smoke test)")
    parser.add_argument("--papers", default="", help="Comma-separated paper-number prefixes (e.g. 001,250)")
    parser.add_argument("--output-dir", default=str(OUT),
                        help="Where to write the normalized layers (default: evaluation/full_v3_normalized)")
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    papers = sorted(path.stem for path in (V2 / "enriched").glob("*.json"))
    limit = args.limit or None
    if args.papers:
        prefixes = tuple(part.strip() for part in args.papers.split(",") if part.strip())
        papers = [paper for paper in papers if paper.startswith(prefixes)]
        limit = None

    frozen = {
        "enriched": {paper: sha256(V2 / "enriched" / f"{paper}.json") for paper in papers},
        "raw": {paper: (sha256(V2 / "raw" / f"{paper}.json")
                        if (V2 / "raw" / f"{paper}.json").exists() else None) for paper in papers},
    }

    built = build(papers, limit)
    registry: ConceptRegistry = built["registry"]
    relations, merged_duplicates = deduplicate_relations(built["relations"])
    counters: Counter = built["counters"]

    zh_applied = apply_language_labels(registry)
    counters["zh_suggested_labels"] = zh_applied

    concepts = registry.to_list()
    type_conflicts = [
        {"concept_id": c["concept_id"], "canonical_name": c["canonical_name"],
         "resolved_type": c["type"], "type_status": c["type_status"],
         "observed_types": c["v2_types"], "papers": c["papers"], "conflicts": c["conflicts"]}
        for c in concepts if c["type_status"] == "conflict_resolved"
    ]
    type_fallbacks = [{"concept_id": c["concept_id"], "canonical_name": c["canonical_name"],
                       "type": c["type"], "v2_types": c["v2_types"]}
                      for c in concepts if c["type_status"] in {"v2_fallback", "type_pending"}]

    alias_index: dict[str, list[dict]] = defaultdict(list)
    for concept in concepts:
        for surface in concept["surface_forms"]:
            alias_index[normalize_key(surface)].append({
                "concept_id": concept["concept_id"], "alias": surface, "kind": "surface",
                "scope": "global", "paper_id": None, "verified": True,
            })
        for alias in concept["aliases"]:
            alias_index[normalize_key(alias["alias"])].append({
                "concept_id": concept["concept_id"], "alias": alias["alias"],
                "kind": alias.get("kind", "surface"), "scope": alias.get("scope", "paper"),
                "paper_id": alias.get("paper_id"), "verified": alias.get("verified", False),
            })

    id_map = {
        "paper_labels": {paper: dict(labels) for paper, labels in built["label_map"].items()},
        "concepts": {concept["concept_id"]: {"canonical_name": concept["canonical_name"],
                                             "type": concept["type"],
                                             "papers": concept["papers"]}
                     for concept in concepts},
        "edges": [{"paper_id": relation["paper_id"], "v2_index": relation["v2_index"],
                   "relation_id": relation["relation_id"]} for relation in relations],
        "instances": {item["instance_id"]: {"paper_id": item["paper_id"], "label": item["label"],
                                            "linked_concept_id": item["linked_concept_id"]}
                      for item in built["instances"]},
    }

    type_counts = Counter(concept["type"] for concept in concepts)
    quality_counts = Counter(concept["quality"] for concept in concepts)
    relation_family_counts = Counter(relation["family"] for relation in relations)
    direction_flags = [relation for relation in relations if not relation["direction_ok"]]
    stats = {
        "version": VERSION,
        "papers": counters["papers"],
        "v2_triples": len(built["raw_relations"]) + counters["observations"] + len(built["numeric_facts"]),
        "numeric_facts": len(built["numeric_facts"]),
        "concepts": len(concepts),
        "concepts_by_type": dict(sorted(type_counts.items())),
        "concepts_by_quality": dict(sorted(quality_counts.items())),
        "concepts_by_type_status": dict(sorted(Counter(c["type_status"] for c in concepts).items())),
        "type_conflicts": len(type_conflicts),
        "type_v2_fallbacks": len(type_fallbacks),
        "concepts_with_zh_label": zh_applied,
        "concepts_merged_across_papers": sum(1 for c in concepts if c["paper_count"] > 1),
        "instances": len(built["instances"]),
        "instances_linked_to_concept": sum(1 for i in built["instances"] if i["linked_concept_id"]),
        "mentions": len(built["mentions"]),
        "mentions_by_kind": dict(Counter(m["mention_kind"] for m in built["mentions"])),
        "value_mentions": counters["value_mentions"],
        "symbol_fragments_excluded": counters["symbol_fragments"],
        "observations": len(built["observations"]),
        "observations_with_value": counters["observations_with_value"],
        "observations_with_unit": counters["observations_with_unit"],
        "observations_with_sample_id": counters["observations_with_sample"],
        "observations_with_conditions": counters["observations_with_conditions"],
        "observation_condition_pairs": counters["observation_condition_pairs"],
        "observations_unmatched_owner": counters["observations_unmatched"],
        "terms_accepted": counters["terms_accepted"],
        "terms_merged": counters["terms_merged"],
        "terms_rejected": counters["terms_rejected"],
        "relations": len(relations),
        "relations_by_family": dict(sorted(relation_family_counts.items())),
        "relations_raw": len(built["raw_relations"]),
        "duplicates_merged": merged_duplicates,
        "composite_relations_added": counters["composite_relations_added"],
        "compound_splits": counters["compound_splits"],
        "targeted_relations": counters["targeted_relations"],
        "direction_flagged": len(direction_flags),
        "paper_aliases_mined": counters["paper_aliases_mined"],
        "embedded_alias_split": counters["embedded_alias_split"],
        "aliases_verified": counters["alias_verified"],
        "alias_index_keys": len(alias_index),
        "fixes_applied": len(built["fixes"]),
        "relations_skipped_nonconcept": counters["relations_skipped_nonconcept"],
        "median_relations_per_paper": statistics.median(
            Counter(r["paper_id"] for r in relations).values()) if relations else 0,
    }

    write_jsonl(output_dir / "concepts.jsonl", concepts)
    write_jsonl(output_dir / "instances.jsonl", built["instances"])
    write_jsonl(output_dir / "mentions.jsonl", built["mentions"])
    write_jsonl(output_dir / "relations.jsonl", relations)
    write_jsonl(output_dir / "relations_raw.jsonl", built["raw_relations"])
    write_jsonl(output_dir / "observations.jsonl", built["observations"])
    write_jsonl(output_dir / "numeric_facts.jsonl", built["numeric_facts"])
    (output_dir / "term_ingest_log.json").write_text(
        json.dumps(built["term_log"], ensure_ascii=False, indent=1), encoding="utf-8")
    (output_dir / "alias_index.json").write_text(json.dumps(alias_index, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
    (output_dir / "id_map.json").write_text(json.dumps(id_map, ensure_ascii=False, indent=1), encoding="utf-8")
    (output_dir / "type_conflicts.json").write_text(json.dumps(type_conflicts, ensure_ascii=False, indent=1),
                                             encoding="utf-8")
    (output_dir / "type_unresolved.json").write_text(json.dumps(type_fallbacks, ensure_ascii=False, indent=1),
                                               encoding="utf-8")
    (output_dir / "fixes_applied.json").write_text(json.dumps(built["fixes"], ensure_ascii=False, indent=1),
                                            encoding="utf-8")
    (output_dir / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8")
    manifest = {
        "run": "full_v3_normalized",
        "version": VERSION,
        "created_from": "evaluation/full_v2/kg_output (frozen)",
        "input_hashes": frozen,
        "source_script": "evaluation/normalize_v3.py",
        "papers": counters["papers"],
        "outputs": ["concepts.jsonl", "instances.jsonl", "mentions.jsonl", "relations.jsonl",
                    "relations_raw.jsonl", "observations.jsonl", "numeric_facts.jsonl", "term_ingest_log.json", "alias_index.json", "id_map.json",
                    "type_conflicts.json", "fixes_applied.json", "stats.json"],
        "notes": [
            "v2 raw/enriched files are read-only inputs; hashes above freeze them",
            "abbreviations become paper-scoped aliases only when the paper defines the expansion",
            "chemical formulas merge only by case-insensitive identity with stoichiometry and phase kept",
            "relation duplicates are merged with all evidence records kept in evidence_all",
            "samples are paper-scoped instances linked to a concept, never global nodes",
        ],
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

    print(json.dumps({key: stats[key] for key in
                      ("papers", "concepts", "concepts_by_quality", "instances", "mentions", "relations",
                       "observations", "duplicates_merged", "compound_splits", "targeted_relations",
                       "direction_flagged", "type_conflicts", "fixes_applied", "concepts_with_zh_label")},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
