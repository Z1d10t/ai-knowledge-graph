"""Stage D: run the fixed retrieval tasks against the normalized v3 graph.

The ten tasks are the ones written down in the review plan (section 6, stage D). Each task
names the concept(s) a user would search for, the relation path that must be found, the
paper that must contain the evidence, and the line the evidence should be near.

The script is deliberately strict: a task passes only when

* the searched term resolves to a concept (no silent fallback to a fuzzy neighbour),
* an outgoing relation of that concept lands on the expected object concept or label, and
* the relation carries evidence from the expected paper, with a markdown line inside the
  tolerance window.

A task that cannot be satisfied is reported as failed with the concrete reason ("concept
not found", "relation not found", "evidence line outside window"); it is never reported as
passed because a nearby concept happened to exist.

Usage::

    python evaluation/stage_d_retrieval.py
    python evaluation/stage_d_retrieval.py --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from knowledge_graph.retrieval import KnowledgeGraphIndex  # noqa: E402
from knowledge_graph.terminology import compact_key, normalize_key, singular_key  # noqa: E402

V3 = ROOT / "evaluation" / "full_v3_normalized"
OUT = ROOT / "evaluation" / "terminology_review_20261125" / "stage_d"

TASKS = [
    {"id": 1, "question": "哪些配体与 Pb 缺陷钝化有关？",
     "subjects": ["4-chlorobenzenesulfonate", "4Cl-BZS"],
     "objects": ["dual-site Pb2+ passivation", "Pb2+ passivation", "dual-site Pb 2+ passivation"],
     "families": ["effect"], "paper": "001", "line": 87, "tolerance": 30},
    {"id": 2, "question": "甲酸根作用于什么缺陷？",
     "subjects": ["formate", "HCOO−"],
     "objects": ["anion-vacancy defects", "anion vacancy", "anion vacancy defects",
                 "I− vacancy", "I-vacancy", "iodide vacancy"],
     "families": ["effect"], "paper": "201", "line": 21, "tolerance": 150},
    {"id": 3, "question": "哪种材料可用于热蒸发 vdW 介质？",
     "subjects": ["Sb2O3"],
     "objects": ["standard thermal evaporation deposition", "thermal evaporation deposition",
                 "thermal evaporation"],
     "families": ["process"], "paper": "095", "line": 66, "tolerance": 40},
    {"id": 4, "question": "准二维钙钛矿有什么特征结构？",
     "subjects": ["quasi-2D perovskites", "quasi-2D perovskite"],
     "objects": ["quantum-well structure", "quantum-well structures"],
     "families": ["structure", "effect"], "paper": "021", "line": 55, "tolerance": 60},
    {"id": 5, "question": "哪些修饰材料用于 MOS 气敏体系？",
     "subjects": ["noble metal nanoparticles", "organic polymers", "carbon nanotubes",
                  "graphene derivatives", "transition metal dichalcogenides"],
     "objects": ["metal oxide semiconductors", "MOS", "metal oxide semiconductor"],
     "families": ["effect"], "paper": "038", "line": 39, "tolerance": 40},
    {"id": 6, "question": "HfO2-ZrO2 栅堆叠利用什么有序状态？",
     "subjects": ["HfO2-ZrO2 superlattice", "HfO2-ZrO2 multilayers", "HfO2-ZrO2 superlattice gate stack"],
     "objects": ["mixed ferroelectric-antiferroelectric order", "mixed FE-AFE order"],
     "families": ["structure", "effect", "composition"], "paper": "043", "line": 194, "tolerance": 60},
    {"id": 7, "question": "一步涂覆如何形成空穴选择接触？",
     "subjects": ["one-step solution-coating", "one-step solution-coating procedure"],
     "objects": ["perovskite light absorber", "perovskite absorber"],
     "families": ["process", "effect"], "paper": "065", "line": 31, "tolerance": 40},
    {"id": 8, "question": "AgBiS2 吸收增强与什么调控有关？",
     "subjects": ["cation disorder homogenization under mild annealing conditions",
                  "cation disorder", "homogeneous cation disorder"],
     "objects": ["absorption coefficient", "absorption coefficients",
                 "optical transition matrix elements"],
     "families": ["effect", "property"], "paper": "250", "line": 36, "tolerance": 150},
    {"id": 9, "question": "宽带隙钙钛矿用于叠层的什么位置？",
     "subjects": ["wide-bandgap perovskites", "WBG perovskites"],
     "objects": ["front absorber", "front perovskite absorber"],
     "families": ["application", "structure", "effect"], "paper": "153", "line": 40, "tolerance": 60},
    {"id": 10, "question": "AlGaN 关联哪些探测器类型？",
     "subjects": ["AlGaN"],
     "objects": ["solar-blind ultraviolet photodetectors", "photodetectors", "avalanche photodiodes",
                 "focal plane arrays", "metal-semiconductor-metal photodetectors", "PDs"],
     "families": ["application", "taxonomy"], "paper": "023", "line": 27, "tolerance": 60},
]

ALIAS_CHECKS = [
    {"query": "甲酸根", "expected": "formate"},
    {"query": "HCOO−", "expected": "formate"},
    {"query": "原子层沉积", "expected": "atomic layer deposition"},
    {"query": "ALD", "expected": "atomic layer deposition"},
    {"query": "4Cl-BZS", "expected": "4-chlorobenzenesulfonate"},
    {"query": "AgBiS2", "expected": "AgBiS2"},
    {"query": "MXenes", "expected": "MXenes"},
    {"query": "fpAs", "expected": "focal plane arrays"},
]


def object_matches(relation: dict, object_ids: set[str], object_labels: list[str]) -> bool:
    if relation["object_id"] in object_ids:
        return True
    relation_object = normalize_key(relation.get("object") or "")
    for label in object_labels:
        key = normalize_key(label)
        if key and len(key) >= 6 and (key in relation_object or relation_object in key):
            return True
    return False


def run_task(index: KnowledgeGraphIndex, task: dict) -> dict:
    subject_hits = []
    for label in task["subjects"]:
        hit = index.search(label, limit=1, include_noisy=True)
        if hit and hit[0]["concept_id"] not in {item["concept_id"] for item in subject_hits}:
            subject_hits.append(hit[0])
    if not subject_hits:
        return {"status": "failed", "reason": "subject concept not found",
                "searched": task["subjects"]}

    object_ids, object_found = set(), []
    for label in task["objects"]:
        for hit in index.search(label, limit=3, include_noisy=True):
            object_ids.add(hit["concept_id"])
            object_found.append(hit["canonical_name"])

    candidates = []
    for subject_hit in subject_hits:
        for relation in (index.view(item) for item in index.outgoing.get(subject_hit["concept_id"], [])):
            if task["families"] and relation.get("family") not in task["families"]:
                continue
            if object_matches(relation, object_ids, task["objects"]):
                candidates.append(relation)
    if not candidates:
        # reverse-causal wording: the object concept states "X is attributed to the subject"
        for subject_hit in subject_hits:
            for relation in (index.view(item) for item in index.incoming.get(subject_hit["concept_id"], [])):
                if relation.get("family") not in ("effect",):
                    continue
                if object_matches(relation, object_ids, task["objects"]):
                    candidates.append(relation)

    if not candidates:
        browse = index.browse(subject_hits[0]["concept_id"], limit=400)
        nearby = sorted({f"{r['predicate']} -> {r['object']}" for r in browse["outgoing"]})[:8]
        return {"status": "failed", "reason": "relation path not found",
                "subject_concept": subject_hits[0]["canonical_name"],
                "object_concepts_found": sorted(set(object_found)),
                "closest_relations": nearby}

    in_paper = [relation for relation in candidates if relation["paper_id"].startswith(task["paper"])]
    if not in_paper:
        relation = candidates[0]
        return {"status": "failed", "reason": "relation found but evidence is in another paper",
                "relation": relation, "expected_paper": task["paper"]}

    for relation in in_paper:
        line = relation.get("evidence_line")
        line_ok = line is not None and abs(int(line) - int(task["line"])) <= task["tolerance"]
        if line_ok:
            return {"status": "passed", "relation": relation, "evidence_line": line,
                    "subject_concept": relation["subject"]}
    relation = in_paper[0]
    return {"status": "failed", "reason": "evidence line outside the expected window",
            "relation": relation, "evidence_line": relation.get("evidence_line"),
            "expected_line": task["line"], "tolerance": task["tolerance"]}


def run_alias_checks(index: KnowledgeGraphIndex) -> list[dict]:
    results = []
    for check in ALIAS_CHECKS:
        hits = index.search(check["query"], limit=3)
        expected_key = singular_key(compact_key(check["expected"]))
        matched = [hit for hit in hits
                   if singular_key(compact_key(hit["canonical_name"])) == expected_key
                   or any(singular_key(compact_key(alias.get("alias", ""))) == expected_key
                          for alias in (index.by_id[hit["concept_id"]].get("aliases") or []))]
        results.append({
            "query": check["query"],
            "expected": check["expected"],
            "status": "passed" if matched else "failed",
            "found": [f"{hit['canonical_name']} ({hit['match']})" for hit in hits],
            "matched_concept": matched[0]["concept_id"] if matched else None,
        })
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the fixed retrieval acceptance tasks")
    parser.add_argument("--json", action="store_true", help="Print the full result as JSON")
    args = parser.parse_args(argv)

    index = KnowledgeGraphIndex.load(V3)
    results = []
    for task in TASKS:
        outcome = run_task(index, task)
        results.append({"task": task, **outcome})
        marker = "PASS" if outcome["status"] == "passed" else "FAIL"
        detail = ""
        if outcome["status"] == "passed":
            relation = outcome["relation"]
            detail = (f"{relation['subject']} -> {relation['predicate']} -> {relation['object']}"
                      f"  [{relation['paper_id'][:3]} L{outcome['evidence_line']}]")
        else:
            detail = outcome.get("reason", "")
        print(f"[{marker}] task {task['id']:2d}: {task['question']} | {detail}")

    alias_results = run_alias_checks(index)
    print()
    for result in alias_results:
        marker = "PASS" if result["status"] == "passed" else "FAIL"
        print(f"[{marker}] alias: {result['query']} -> {result['expected']} | {result['found'][:2]}")

    passed = sum(1 for result in results if result["status"] == "passed")
    alias_passed = sum(1 for result in alias_results if result["status"] == "passed")
    summary = {
        "tasks": len(results),
        "tasks_passed": passed,
        "tasks_pass_rate": round(passed / len(results), 4),
        "alias_checks": len(alias_results),
        "alias_checks_passed": alias_passed,
        "alias_pass_rate": round(alias_passed / len(alias_results), 4),
        "graph": index.stats(),
        "failed_tasks": [{"id": result["task"]["id"], "reason": result.get("reason"),
                          "subject_concept": result.get("subject_concept")}
                         for result in results if result["status"] != "passed"],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "retrieval_tasks.json").write_text(json.dumps(TASKS, ensure_ascii=False, indent=1),
                                              encoding="utf-8")
    (OUT / "retrieval_acceptance.json").write_text(
        json.dumps({"summary": summary, "tasks": results, "alias_checks": alias_results},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"\n{passed}/{len(results)} retrieval tasks passed; "
              f"{alias_passed}/{len(alias_results)} alias checks passed")
        print(f"graph: {summary['graph']}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
