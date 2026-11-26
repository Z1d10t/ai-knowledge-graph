"""Lookup layer over the normalized v3 graph (concepts, aliases, relations, evidence).

The review plan requires four user-facing operations -- term search, alias search,
relation browsing and evidence navigation -- to work on the concept layer rather than on
raw model strings. This module implements them without a server:

>>> index = KnowledgeGraphIndex.load("evaluation/full_v3_normalized")
>>> index.search("甲酸根")[0]["canonical_name"]
'formate'
>>> step = index.browse(index.search("formate")[0]["concept_id"])
>>> [(r["predicate"], r["object"]) for r in step["outgoing"]][:2]
[('eliminates', 'anion-vacancy defects'), ...]

Design rules:

* search never merges concepts; it returns ranked matches with the matched alias and the
  match kind, so an ambiguous abbreviation is visible instead of silent;
* fragment/symbol concepts are hidden by default but reachable with ``include_noisy=True``;
* every relation returned carries its evidence sentence, paper and markdown line so the UI
  can jump to the source text.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from knowledge_graph.terminology import (
    clean_text,
    classify_type,
    formula_identity,
    identity_key,
    normalize_key,
)

_CJK_RE = re.compile(r"[\u3400-\u9fff]")


def _rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


class KnowledgeGraphIndex:
    """In-memory index of a normalized v3 directory."""

    def __init__(self, concepts: list[dict], relations: list[dict], aliases: dict[str, list[dict]],
                 instances: list[dict] | None = None, observations: list[dict] | None = None,
                 directory: Path | None = None) -> None:
        self.directory = directory
        self.concepts = concepts
        self.relations = relations
        self.aliases = aliases
        self.instances = instances or []
        self.observations = observations or []
        self.by_id = {concept["concept_id"]: concept for concept in concepts}
        self.outgoing: dict[str, list[dict]] = defaultdict(list)
        self.incoming: dict[str, list[dict]] = defaultdict(list)
        for relation in relations:
            self.outgoing[relation["subject_id"]].append(relation)
            self.incoming[relation["object_id"]].append(relation)
        self.instances_by_concept: dict[str, list[dict]] = defaultdict(list)
        for instance in self.instances:
            if instance.get("linked_concept_id"):
                self.instances_by_concept[instance["linked_concept_id"]].append(instance)
        self.observations_by_concept: dict[str, list[dict]] = defaultdict(list)
        for observation in self.observations:
            if observation.get("property_concept_id"):
                self.observations_by_concept[observation["property_concept_id"]].append(observation)
        self._zh: dict[str, list[str]] = defaultdict(list)
        for concept in concepts:
            zh = (concept.get("language_labels") or {}).get("zh_suggested")
            if zh:
                self._zh[zh].append(concept["concept_id"])

    # -- loading ---------------------------------------------------------
    @classmethod
    def load(cls, directory: str | Path) -> KnowledgeGraphIndex:
        directory = Path(directory)
        concepts = _rows(directory / "concepts.jsonl")
        relations = _rows(directory / "relations.jsonl")
        alias_path = directory / "alias_index.json"
        aliases = json.loads(alias_path.read_text(encoding="utf-8")) if alias_path.exists() else {}
        return cls(concepts, relations, aliases,
                   instances=_rows(directory / "instances.jsonl"),
                   observations=_rows(directory / "observations.jsonl"),
                   directory=directory)

    # -- search ----------------------------------------------------------
    def search(self, query: str, limit: int = 10, include_noisy: bool = False,
               type_filter: str | None = None) -> list[dict]:
        """Ranked concept matches for a term, an alias, a formula or a Chinese label."""
        text = clean_text(query or "").strip()
        if not text:
            return []
        key = normalize_key(text)
        formula = formula_identity(text)
        scored: dict[str, dict] = {}

        def consider(concept_id: str, score: float, match: str, alias: str | None = None) -> None:
            concept = self.by_id.get(concept_id)
            if concept is None:
                return
            if type_filter and concept["type"] != type_filter:
                return
            if not include_noisy and concept.get("quality", "clean") not in {"clean", "instrument"}:
                return
            current = scored.get(concept_id)
            if current is None or score > current["score"]:
                scored[concept_id] = {
                    "concept_id": concept_id,
                    "canonical_name": concept["canonical_name"],
                    "type": concept["type"],
                    "quality": concept.get("quality"),
                    "paper_count": concept.get("paper_count", 0),
                    "mention_count": concept.get("mention_count", 0),
                    "zh_suggested": (concept.get("language_labels") or {}).get("zh_suggested"),
                    "score": score,
                    "match": match,
                    "matched_alias": alias,
                }

        # 1. exact alias / surface key
        for entry in self.aliases.get(key, []):
            consider(entry["concept_id"], 100.0, f"alias:{entry.get('kind', 'surface')}", entry.get("alias"))
        # 2. exact canonical name
        for concept in self.concepts:
            if concept["canonical_name"].lower() == text.lower():
                consider(concept["concept_id"], 98.0, "name")
        # 3. chemical formula identity
        if formula:
            for concept in self.concepts:
                if concept.get("formula") and formula_identity(concept["canonical_name"]) == formula:
                    consider(concept["concept_id"], 95.0, "formula")
        # 4. Chinese suggested label
        if _CJK_RE.search(text):
            for concept_id in self._zh.get(text, []):
                consider(concept_id, 94.0, "zh_label")
            for zh, concept_ids in self._zh.items():
                if text in zh or zh in text:
                    for concept_id in concept_ids:
                        consider(concept_id, 70.0, "zh_partial", zh)
        # 5. containment in an alias / canonical name
        if len(key) >= 4:
            for alias_key, entries in self.aliases.items():
                if key in alias_key or (len(alias_key) >= 4 and alias_key in key):
                    for entry in entries:
                        consider(entry["concept_id"], 60.0 if key in alias_key else 55.0,
                                 "alias_partial", entry.get("alias"))
        # 6. token overlap on canonical names
        if key:
            tokens = [t for t in re.findall(r"[a-z0-9]{4,}", text.lower())]
            for concept in self.concepts:
                name = concept["canonical_name"].lower()
                if tokens and all(token in name for token in tokens):
                    consider(concept["concept_id"], 40.0, "token")

        results = sorted(scored.values(), key=lambda item: (-item["score"], -item["paper_count"],
                                                            len(item["canonical_name"])))
        return results[:limit]

    def resolve(self, label: str) -> dict | None:
        """Best concept for a label (first search hit), used by relation checks."""
        hits = self.search(label, limit=1, include_noisy=True)
        return hits[0] if hits else None

    # -- browsing --------------------------------------------------------
    def browse(self, concept_id: str, limit: int = 100) -> dict | None:
        """Concept card: aliases, outgoing and incoming relations, samples, observations."""
        concept = self.by_id.get(concept_id)
        if concept is None:
            return None
        outgoing = sorted(self.outgoing.get(concept_id, []),
                          key=lambda r: (-r.get("duplicate_count", 1), r["predicate"]))[:limit]
        incoming = sorted(self.incoming.get(concept_id, []),
                          key=lambda r: (-r.get("duplicate_count", 1), r["predicate"]))[:limit]
        return {
            "concept": concept,
            "aliases": concept.get("aliases", []),
            "outgoing": [self._relation_view(relation) for relation in outgoing],
            "incoming": [self._relation_view(relation) for relation in incoming],
            "instances": self.instances_by_concept.get(concept_id, [])[:20],
            "observations": self.observations_by_concept.get(concept_id, [])[:20],
        }

    def relations_between(self, subject_id: str, object_id: str) -> list[dict]:
        return [relation for relation in self.outgoing.get(subject_id, [])
                if relation["object_id"] == object_id]

    def find_relation(self, subject_label: str, predicate_any: list[str] | None = None,
                      object_labels: list[str] | None = None,
                      families: list[str] | None = None) -> list[dict]:
        """Relations from a subject concept that land on any of the object labels."""
        subject = self.resolve(subject_label)
        if not subject:
            return []
        object_ids = set()
        for label in object_labels or []:
            for hit in self.search(label, limit=5, include_noisy=True):
                object_ids.add(hit["concept_id"])
        results = []
        for relation in self.outgoing.get(subject["concept_id"], []):
            if object_ids and relation["object_id"] not in object_ids:
                continue
            if families and relation.get("family") not in families:
                continue
            if predicate_any and relation["predicate"].lower() not in {p.lower() for p in predicate_any}:
                continue
            results.append(self._relation_view(relation))
        return results

    def _relation_view(self, relation: dict) -> dict:
        return {
            "relation_id": relation.get("relation_id"),
            "paper_id": relation.get("paper_id"),
            "subject_id": relation.get("subject_id"),
            "object_id": relation.get("object_id"),
            "subject": relation.get("subject_label"),
            "predicate": relation.get("predicate"),
            "object": relation.get("object_label"),
            "family": relation.get("family"),
            "evidence": relation.get("evidence"),
            "evidence_line": relation.get("evidence_line"),
            "polarity": relation.get("polarity"),
            "modality": relation.get("modality"),
            "direction_ok": relation.get("direction_ok"),
            "duplicate_count": relation.get("duplicate_count", 1),
            "review_status": relation.get("review_status"),
            "source": relation.get("source"),
            "evidence_all": relation.get("evidence_all", []),
        }

    def view(self, relation: dict) -> dict:
        """Public relation view (stable keys for callers and the UI)."""
        return self._relation_view(relation)

    # -- statistics ------------------------------------------------------
    def stats(self) -> dict:
        return {
            "concepts": len(self.concepts),
            "relations": len(self.relations),
            "aliases": len(self.aliases),
            "instances": len(self.instances),
            "observations": len(self.observations),
            "papers": len({relation["paper_id"] for relation in self.relations}),
        }

    def describe(self, concept_id: str) -> str:
        """One-line human summary used by the acceptance report."""
        concept = self.by_id.get(concept_id)
        if not concept:
            return ""
        zh = (concept.get("language_labels") or {}).get("zh_suggested") or ""
        return (f"{concept['canonical_name']} [{concept['type']}]"
                + (f" / {zh}" if zh else "")
                + f" ({concept.get('paper_count', 0)} papers, {concept.get('mention_count', 0)} mentions)")


def label_identity(label: str) -> str:
    """Identity key of a bare label (helper for callers building ad-hoc queries)."""
    return identity_key(label, classify_type(label)[0])
