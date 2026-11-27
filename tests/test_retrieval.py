"""Tests for the retrieval layer over a small synthetic v3 graph."""
import json
from pathlib import Path

import pytest

from knowledge_graph.retrieval import KnowledgeGraphIndex


def _write(path: Path, rows):
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


@pytest.fixture()
def index(tmp_path):
    concepts = [
        {"concept_id": "c-formate", "canonical_name": "formate", "type": "material",
         "quality": "clean", "paper_count": 1, "mention_count": 3, "formula": None,
         "aliases": [{"alias": "HCOO−", "scope": "paper", "paper_id": "p1",
                      "kind": "abbreviation", "verified": True}],
         "surface_forms": {"formate": 2, "HCOO−": 1},
         "papers": ["p1"], "language_labels": {"zh_suggested": "甲酸根"}, "conflicts": []},
        {"concept_id": "c-vacancy", "canonical_name": "anion-vacancy defects", "type": "defect",
         "quality": "clean", "paper_count": 1, "mention_count": 2, "formula": None,
         "aliases": [], "surface_forms": {"anion-vacancy defects": 2}, "papers": ["p1"],
         "language_labels": {}, "conflicts": []},
        {"concept_id": "c-fragment", "canonical_name": "which effects the purity of GaN",
         "type": "material", "quality": "fragment", "paper_count": 1, "mention_count": 1,
         "formula": None, "aliases": [], "surface_forms": {"which effects the purity of GaN": 1},
         "papers": ["p1"], "language_labels": {}, "conflicts": []},
    ]
    relations = [
        {"relation_id": "r1", "paper_id": "p1", "subject_id": "c-formate",
         "object_id": "c-vacancy", "subject_label": "formate", "object_label": "anion-vacancy defects",
         "predicate": "eliminates", "family": "effect", "evidence": "HCOO− eliminates vacancy defects",
         "evidence_line": 79, "polarity": "positive", "modality": "asserted", "direction_ok": True,
         "duplicate_count": 2, "review_status": "machine", "source": "v2_enriched",
         "evidence_all": [{"evidence": "a", "evidence_line": 79, "chunk": 1, "v2_index": 1}]},
    ]
    aliases = {
        "formate": [{"concept_id": "c-formate", "alias": "formate", "kind": "surface",
                     "scope": "global", "paper_id": None, "verified": True}],
        "hcoo": [{"concept_id": "c-formate", "alias": "HCOO−", "kind": "abbreviation",
                  "scope": "paper", "paper_id": "p1", "verified": True}],
    }
    instances = [{"instance_id": "i1", "paper_id": "p1", "label": "control device",
                  "type": "sample", "linked_concept_id": "c-formate"}]
    observations = [{"observation_id": "obs-1", "paper_id": "p1",
                     "property_concept_id": "c-formate", "property": "fill factor", "value": "86.2%"}]

    _write(tmp_path / "concepts.jsonl", concepts)
    _write(tmp_path / "relations.jsonl", relations)
    _write(tmp_path / "instances.jsonl", instances)
    _write(tmp_path / "observations.jsonl", observations)
    (tmp_path / "alias_index.json").write_text(json.dumps(aliases), encoding="utf-8")
    return KnowledgeGraphIndex.load(tmp_path)


def test_search_by_alias_and_chinese_label(index):
    assert index.search("HCOO−")[0]["canonical_name"] == "formate"
    assert index.search("甲酸根")[0]["canonical_name"] == "formate"
    assert index.search("formate")[0]["concept_id"] == "c-formate"


def test_search_hides_noisy_concepts_by_default(index):
    assert all(hit["canonical_name"] != "which effects the purity of GaN"
               for hit in index.search("effects the purity", limit=5))
    assert any(hit["canonical_name"] == "which effects the purity of GaN"
               for hit in index.search("effects the purity", limit=5, include_noisy=True))


def test_browse_returns_evidence_and_relations(index):
    card = index.browse("c-formate")
    assert card["concept"]["canonical_name"] == "formate"
    assert card["outgoing"][0]["predicate"] == "eliminates"
    assert card["outgoing"][0]["evidence_line"] == 79
    assert card["instances"][0]["instance_id"] == "i1"
    assert card["observations"][0]["value"] == "86.2%"


def test_relation_view_and_search_limit(index):
    relations = index.view(index.relations[0])
    assert relations["subject"] == "formate" and relations["object"] == "anion-vacancy defects"
    assert len(index.search("formate", limit=1)) == 1


def test_stats(index):
    stats = index.stats()
    assert stats["concepts"] == 3 and stats["relations"] == 1
