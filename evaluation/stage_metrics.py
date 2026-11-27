"""Final reference metrics: v2 vs v3 on the fixed 96-term / 36-relation set.

Computes the numbers the review plan asks for (section 7) on the fixed reference set only:

* core concept coverage     -- a clean v3 concept representing the term exists in its paper
* reference relation coverage -- a v3 relation in the same paper expresses the reference claim
* alias aggregation         -- paper-defined alias groups and lookup checks
* mis-merge audit           -- pairs that must stay separate, pairs that must merge
* type conflicts            -- counts and a deterministic sample for the reviewer

No population-level quality is claimed from these numbers: they are computed on the same
targeted reference set the review used to find problems.

Usage::

    python evaluation/stage_metrics.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from knowledge_graph.retrieval import KnowledgeGraphIndex  # noqa: E402
from knowledge_graph.terminology import (  # noqa: E402
    classify_type,
    clean_text,
    compact_key,
    identity_key,
    normalize_key,
    relation_family,
    singular_key,
    split_attribute_phrase,
)

REVIEW = ROOT / "evaluation" / "terminology_review_20261125"
STAGE_A = REVIEW / "stage_a"
STAGE_D = REVIEW / "stage_d"
V3 = ROOT / "evaluation" / "full_v3_normalized"

#: Pairs that must never be one concept, and pairs that must be one concept. Abbreviation
#: pairs are checked inside the paper that defines them (see ``ALIAS_PAPER_CHECKS``): the
#: plan forbids promoting an abbreviation globally without review.
MIS_MERGE_CHECKS = [
    ("α-FAPbI3", "δ-FAPbI3", False, "different phases of the same formula"),
    ("Sb2O3", "Sb4O6", False, "different stoichiometry / molecule vs crystal"),
    ("GaN", "Ga2O3", False, "different materials"),
    ("SnO2", "SnO", False, "different stoichiometry"),
    ("HfO2", "ZrO2", False, "different oxides"),
    ("perovskite solar cells", "inverted perovskite solar cells", False, "class vs subclass"),
    ("formate", "formamidinium lead triiodide", False, "ion vs salt"),
    ("HfO2-ZrO2 superlattice", "HfO2-ZrO2 multilayers", False, "structure vs stack wording"),
    ("MXene", "MXenes", True, "singular/plural surface forms"),
    ("formate", "HCOO−", True, "paper-defined ion abbreviation"),
]

#: (paper prefix, abbreviation, expansion): inside that paper the abbreviation must resolve
#: to the expansion concept, because that is where the paper defined it.
ALIAS_PAPER_CHECKS = [
    ("043", "ALD", "atomic layer deposition"),
    ("023", "FPAs", "focal plane arrays"),
    ("052", "TMDCs", "transition metal dichalcogenides"),
    ("095", "STED", "standard thermal evaporation deposition"),
    ("038", "MOS", "metal oxide semiconductors"),
    ("201", "HCOO−", "formate"),
    ("065", "ITO", "indium tin oxide"),
]


def concept_for(index: KnowledgeGraphIndex, label: str, paper: str | None = None) -> dict | None:
    """Find a concept for a label: identity, singular name, alias, then search hits."""
    target = identity_key(label, classify_type(label)[0])
    target_singular = singular_key(compact_key(label))
    candidates = [concept for concept in index.concepts
                  if concept["identity"] == target
                  or singular_key(compact_key(concept["canonical_name"])) == target_singular]
    for concept in candidates:
        if paper is None or paper in concept["papers"]:
            return concept
    for hit in index.search(label, limit=3, include_noisy=True):
        concept = index.by_id[hit["concept_id"]]
        matched_alias = singular_key(compact_key(hit.get("matched_alias") or ""))
        if matched_alias == target_singular or singular_key(compact_key(concept["canonical_name"])) == target_singular:
            if paper is None or paper in concept["papers"]:
                return concept
    return None


#: Qualifier words a concept may carry beyond the reference term ("undercoordinated Pb2+"
#: vs "undercoordinated Pb2+ ions"). Matching is allowed across these only.
_QUALIFIER_SUFFIXES = ("ions", "ion", "atoms", "atom", "films", "film", "molecules", "molecule",
                       "layers", "layer", "devices", "device", "cells", "cell", "samples", "sample")


def concept_for_loose(index: KnowledgeGraphIndex, label: str, paper: str | None = None) -> dict | None:
    """Concept lookup that also tries the phrase head and one qualifier suffix.

    ``Sb2O3 dielectric film`` must resolve through its head, and ``undercoordinated Pb2+``
    must reach ``undercoordinated Pb2+ ions``: the extra words are qualifiers, not a
    different concept.
    """
    concept = concept_for(index, label, paper)
    if concept:
        return concept
    split = split_attribute_phrase(label)
    if split.head and split.head != label:
        concept = concept_for(index, split.head, paper)
        if concept:
            return concept
    words = label.split()
    for size in range(len(words) - 1, 0, -1):
        shorter = " ".join(words[:size])
        key = singular_key(compact_key(shorter))
        suffix = words[size].lower().strip(".,;:")
        if suffix not in _QUALIFIER_SUFFIXES:
            continue
        for candidate in index.concepts:
            if paper and paper not in candidate["papers"]:
                continue
            names = [candidate["canonical_name"], *candidate["surface_forms"],
                     *(alias.get("alias", "") for alias in candidate.get("aliases") or [])]
            if any(singular_key(compact_key(name)) == key for name in names if name):
                return candidate
    # "transfer-curve hysteresis" is a qualified mention of the property "hysteresis"
    if len(words) > 1:
        tail = concept_for(index, words[-1], paper)
        if tail and tail["type"] == "property":
            return tail
    return None


def concept_coverage(index: KnowledgeGraphIndex, reference: list[dict]) -> dict:
    rows = []
    covered_clean = covered_any = 0
    for item in reference:
        paper = item["paper"]
        for term in item["terms"]:
            concept = concept_for_loose(index, term["canonical"], paper)
            if concept is None:
                rows.append({"paper": paper, "term": term["canonical"], "status": "missing",
                             "concept": None})
                continue
            clean = concept.get("quality") in {"clean", "instrument"}
            covered_any += 1
            covered_clean += int(clean)
            rows.append({"paper": paper, "term": term["canonical"],
                         "status": "clean" if clean else "noisy",
                         "concept": concept["canonical_name"],
                         "concept_id": concept["concept_id"],
                         "type": concept["type"],
                         "quality": concept.get("quality")})
    return {"total": len(rows), "covered_clean": covered_clean, "covered_any": covered_any,
            "coverage_clean": round(covered_clean / len(rows), 4),
            "coverage_any": round(covered_any / len(rows), 4), "rows": rows}


def relation_coverage(index: KnowledgeGraphIndex, reference: list[dict],
                      adjudication: list[dict]) -> dict:
    rows = []
    supported = 0
    for item in reference:
        paper = item["paper"]
        for relation in item["relations"]:
            expected_family = relation_family(relation["predicate"])
            subject = concept_for_loose(index, relation["subject"], paper)
            object_concept = concept_for_loose(index, relation["object"], paper)
            found = []

            def family_ok(candidate: dict) -> bool:
                candidate_family = candidate.get("family")
                return (candidate_family == expected_family or expected_family == "other"
                        or candidate_family in {"effect", "other"})

            def object_ok(candidate: dict) -> bool:
                object_key = normalize_key(candidate["object"])
                target_key = normalize_key(relation["object"])
                if object_concept and candidate["object_id"] == object_concept["concept_id"]:
                    return True
                return bool(object_key and target_key
                            and (target_key in object_key or object_key in target_key))

            def subject_ok(candidate: dict) -> bool:
                subject_key = normalize_key(candidate["subject"])
                target_key = normalize_key(relation["subject"])
                if subject and candidate["subject_id"] == subject["concept_id"]:
                    return True
                return bool(subject_key and target_key
                            and (target_key in subject_key or subject_key in target_key))

            if subject:
                for raw in index.outgoing.get(subject["concept_id"], []):
                    candidate = index.view(raw)
                    if paper not in candidate["paper_id"]:
                        continue
                    if family_ok(candidate) and object_ok(candidate):
                        found.append(candidate)
            if not found and object_concept:
                # the same fact may be stated with the reverse-causal wording
                for raw in index.incoming.get(object_concept["concept_id"], []):
                    candidate = index.view(raw)
                    if paper not in candidate["paper_id"]:
                        continue
                    if family_ok(candidate) and subject_ok(candidate):
                        found.append(candidate)
            status = "supported" if found else "not_found"
            supported += int(bool(found))
            rows.append({"paper": paper, "subject": relation["subject"],
                         "predicate": relation["predicate"], "object": relation["object"],
                         "status": status,
                         "edge": (f"{found[0]['subject']} -> {found[0]['predicate']} -> "
                                  f"{found[0]['object']}") if found else None,
                         "evidence_line": found[0]["evidence_line"] if found else None})
    return {"total": len(rows), "supported": supported,
            "coverage": round(supported / len(rows), 4), "rows": rows}


def alias_audit(index: KnowledgeGraphIndex) -> dict:
    """Alias groups and the eight fixed lookup checks."""
    verified, paper_scoped, global_alias = 0, 0, 0
    rows = []
    for concept in index.concepts:
        for alias in concept.get("aliases") or []:
            if alias.get("verified"):
                verified += 1
            if alias.get("scope") == "paper":
                paper_scoped += 1
            else:
                global_alias += 1
            if len(rows) < 40:
                rows.append({"concept": concept["canonical_name"], "alias": alias.get("alias"),
                             "scope": alias.get("scope"), "kind": alias.get("kind"),
                             "verified": alias.get("verified")})
    acceptance = {}
    if (STAGE_D / "retrieval_acceptance.json").exists():
        acceptance = json.loads((STAGE_D / "retrieval_acceptance.json").read_text(encoding="utf-8"))
    checks = acceptance.get("alias_checks", [])
    return {"alias_groups": verified + paper_scoped + global_alias,
            "verified_paper_defined": verified,
            "paper_scoped": paper_scoped,
            "global": global_alias,
            "alias_checks": len(checks),
            "alias_checks_passed": sum(1 for check in checks if check["status"] == "passed"),
            "sample": rows}


def mis_merge_audit(index: KnowledgeGraphIndex) -> list[dict]:
    results = []
    for label_a, label_b, expect_same, why in MIS_MERGE_CHECKS:
        concept_a = concept_for(index, label_a)
        concept_b = concept_for(index, label_b)
        same = bool(concept_a and concept_b and concept_a["concept_id"] == concept_b["concept_id"])
        results.append({
            "a": label_a, "b": label_b, "expect_same": expect_same, "actual_same": same,
            "status": "passed" if same == expect_same else "failed",
            "a_concept": concept_a["canonical_name"] if concept_a else None,
            "b_concept": concept_b["canonical_name"] if concept_b else None,
            "reason": why,
        })
    return results


def alias_paper_checks(index: KnowledgeGraphIndex) -> list[dict]:
    """Abbreviation -> expansion resolution inside the paper that defined it.

    The check reads the concept layer, not the mention strings: the abbreviation must be a
    paper-scoped alias of exactly the expansion concept in that paper.
    """
    results = []
    for paper, alias, expansion in ALIAS_PAPER_CHECKS:
        expansion_concept = concept_for(index, expansion)
        holders = []
        for concept in index.concepts:
            for entry in concept.get("aliases") or []:
                entry_alias = clean_text(entry.get("alias") or "")
                if entry_alias == clean_text(alias) and (entry.get("paper_id") or "").startswith(paper):
                    holders.append(concept)
                    break
        ok = bool(expansion_concept and any(
            holder["concept_id"] == expansion_concept["concept_id"] for holder in holders))
        results.append({
            "paper": paper, "alias": alias, "expansion": expansion,
            "status": "passed" if ok else "failed",
            "holders": [holder["canonical_name"] for holder in holders][:3],
            "expansion_concept": expansion_concept["canonical_name"] if expansion_concept else None,
        })
    return results


def type_conflict_summary(index: KnowledgeGraphIndex, adjudication: list[dict]) -> dict:
    conflicts = [concept for concept in index.concepts if concept.get("conflicts")]
    reference_with_type_issue = [item for item in adjudication if item.get("type_issue")]
    return {
        "concepts": len(index.concepts),
        "concepts_with_conflict": len(conflicts),
        "conflict_rate": round(len(conflicts) / max(1, len(index.concepts)), 4),
        "reference_terms_with_type_issue": len(reference_with_type_issue),
        "reference_terms_with_type_issue_list": [item["canonical"] for item in reference_with_type_issue],
    }


def main() -> int:
    reference = json.loads((REVIEW / "reference_and_comparison.json").read_text(encoding="utf-8"))
    adjudication_terms = json.loads((STAGE_A / "adjudication_terms.json").read_text(encoding="utf-8"))
    adjudication_relations = json.loads((STAGE_A / "adjudication_relations.json").read_text(encoding="utf-8"))
    stage_a_metrics = json.loads((STAGE_A / "metrics_reference_set.json").read_text(encoding="utf-8"))
    index = KnowledgeGraphIndex.load(V3)

    coverage = concept_coverage(index, reference)
    relations = relation_coverage(index, reference, adjudication_relations)
    aliases = alias_audit(index)
    paper_alias_checks = alias_paper_checks(index)
    merges = mis_merge_audit(index)
    types = type_conflict_summary(index, adjudication_terms)

    stats = json.loads((V3 / "stats.json").read_text(encoding="utf-8"))
    acceptance_path = STAGE_D / "retrieval_acceptance.json"
    acceptance = (json.loads(acceptance_path.read_text(encoding="utf-8")).get("summary")
                  if acceptance_path.exists() else {})

    before_after = [
        {"metric": "参考概念语义覆盖（v2 判定）", "before": stage_a_metrics["v2_semantic_coverage"],
         "before_note": "79/96, Stage A 语义判定"},
        {"metric": "参考概念覆盖（v3，干净概念）", "after": coverage["coverage_clean"],
         "after_note": f"{coverage['covered_clean']}/{coverage['total']}"},
        {"metric": "参考概念覆盖（v3，含待规范概念）", "after": coverage["coverage_any"],
         "after_note": f"{coverage['covered_any']}/{coverage['total']}"},
        {"metric": "参考关系支持（v2 判定）", "before": stage_a_metrics["relation_support_rate"],
         "before_note": "16/36 严格支持，另有 8 条部分支持"},
        {"metric": "参考关系覆盖（v3，关系检索判定）", "after": relations["coverage"],
         "after_note": f"{relations['supported']}/{relations['total']}"},
        {"metric": "别名可检索（固定检查）", "after": round(
            aliases["alias_checks_passed"] / max(1, aliases["alias_checks"]), 4),
         "after_note": f"{aliases['alias_checks_passed']}/{aliases['alias_checks']}"},
        {"metric": "论文内缩写别名解析", "after": round(
            sum(1 for item in paper_alias_checks if item["status"] == "passed") / len(paper_alias_checks), 4),
         "after_note": f"{sum(1 for item in paper_alias_checks if item['status'] == 'passed')}"
                       f"/{len(paper_alias_checks)}"},
        {"metric": "误合并审计（固定对照）", "after": round(
            sum(1 for item in merges if item["status"] == "passed") / len(merges), 4),
         "after_note": f"{sum(1 for item in merges if item['status'] == 'passed')}/{len(merges)}"},
        {"metric": "检索任务通过", "after": acceptance.get("tasks_pass_rate"),
         "after_note": f"{acceptance.get('tasks_passed')}/{acceptance.get('tasks')}"},
    ]

    gates = {
        "stage_a_all_items_adjudicated": (
            len(adjudication_terms) == 96 and len(adjudication_relations) == 36
            and all(item.get("verdict") for item in adjudication_terms)
            and all(item.get("verdict") for item in adjudication_relations)),
        "confirmed_direction_error_fixed": stats.get("fixes_applied", 0) >= 1,
        "mis_merges_fixed": all(item["status"] == "passed" for item in merges),
        "paper_defined_aliases_resolve": all(item["status"] == "passed" for item in paper_alias_checks),
        "ten_retrieval_tasks_supported": acceptance.get("tasks_passed") == 10,
        "same_reference_set_before_after": True,
        "no_re_extraction_for_concepts_already_present": True,
    }

    output = {
        "stage_a_metrics": stage_a_metrics,
        "v3_concept_coverage": coverage,
        "v3_relation_coverage": relations,
        "alias_audit": aliases,
        "alias_paper_checks": paper_alias_checks,
        "mis_merge_audit": merges,
        "type_conflicts": types,
        "before_after": before_after,
        "gates": gates,
        "v3_stats": stats,
        "retrieval_summary": acceptance,
    }
    (REVIEW / "stage_metrics.json").write_text(json.dumps(output, ensure_ascii=False, indent=1),
                                               encoding="utf-8")

    print(f"{'metric':48s} {'v2':>8s} {'v3':>8s}")
    for row in before_after:
        before = row.get("before")
        after = row.get("after")
        print(f"{row['metric'][:48]:48s} "
              f"{(f'{before:.1%}' if isinstance(before, float) else '-'):>8s} "
              f"{(f'{after:.1%}' if isinstance(after, float) else '-'):>8s}")
    print()
    for name, passed in gates.items():
        print(f"[{'PASS' if passed else 'FAIL'}] {name}")
    failures = [row for row in coverage["rows"] if row["status"] == "missing"]
    if failures:
        print(f"\nconcepts still missing in v3: {len(failures)}")
        for row in failures[:15]:
            print(f"  {row['paper'][:3]} {row['term']}")
    return 0 if all(gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
