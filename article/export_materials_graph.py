#!/usr/bin/env python3
"""Export the normalized v3 graph into a self-contained interactive delivery package.

One entry point produces everything the delivery needs:

    triples_full.csv / triples_full.jsonl   every normalized relation, one row each
    nodes.jsonl                             concepts + paper-scoped instances
    data/                                   compact browser data (nodes, edges, search,
                                            overview, adjacency, per-paper evidence shards)
    index.html + assets/                    the offline interactive page
    manifest.json                           input version, counts, checks, file hashes
    materials_kg_overview.png               global summary figure
    README_打开方式.md                      how to open and what the numbers mean

The script never reads the network and never re-extracts text. It validates the v3
primary keys and endpoints, refuses to publish a half-written package (staging +
verification), and keeps both endpoints as stable v3 ids so paper-scoped samples never
collapse into a global node.

Usage::

    python article/export_materials_graph.py \\
        --input-dir evaluation/full_v3_normalized \\
        --papers-dir "../材料论文/全部_285篇/md" \\
        --output-dir delivery/materials_kg_baseline

    python article/export_materials_graph.py --verify-only --output-dir delivery/materials_kg_baseline
    python article/export_materials_graph.py --attach-png delivery/materials_kg_baseline/materials_kg_overview.png \\
        --output-dir delivery/materials_kg_baseline
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from knowledge_graph.terminology import clean_text, normalize_key  # noqa: E402

DEFAULT_INPUT = ROOT / "evaluation" / "full_v3_normalized"
DEFAULT_PAPERS = ROOT.parent / "材料论文" / "全部_285篇" / "md"
TEMPLATES = ROOT / "src" / "knowledge_graph" / "templates"

TYPE_ORDER = ["material", "material_class", "component", "structure", "defect", "process",
              "characterization", "mechanism", "property", "device", "interface", "sample"]
TYPE_LABELS = {
    "material": "材料", "material_class": "材料类别", "component": "功能层/部件",
    "structure": "结构/晶相", "defect": "缺陷", "process": "工艺/处理",
    "characterization": "表征/计算", "mechanism": "机理/过程", "property": "性能/物理量",
    "device": "器件", "interface": "界面", "sample": "样品/实例",
}
TYPE_LABELS_EN = {
    "material": "Material", "material_class": "Material class", "component": "Layer / part",
    "structure": "Structure / phase", "defect": "Defect", "process": "Process",
    "characterization": "Characterization", "mechanism": "Mechanism", "property": "Property",
    "device": "Device", "interface": "Interface", "sample": "Sample / instance",
}
TYPE_COLORS = {
    "material": "#4e79a7", "material_class": "#59a14f", "component": "#f28e2b",
    "structure": "#b07aa1", "defect": "#e15759", "process": "#76b7b2",
    "characterization": "#edc948", "mechanism": "#ff9da7", "property": "#9c755f",
    "device": "#8c8c8c", "interface": "#8cd17d", "sample": "#a0cbe8",
}
FAMILY_LABELS_EN = {
    "effect": "Effect", "process": "Process", "dependency": "Dependency",
    "characterization": "Characterization", "taxonomy": "Taxonomy", "application": "Application",
    "composition": "Composition", "structure": "Structure", "phase_transition": "Phase transition",
    "other": "Other",
}
FAMILY_LABELS = {
    "effect": "作用/影响", "process": "制备/处理", "dependency": "依赖/条件",
    "characterization": "表征/计算", "taxonomy": "分类", "application": "应用/功能",
    "composition": "组成", "structure": "结构", "phase_transition": "相变", "other": "其他",
}
CSV_FIELDS = ["relation_id", "subject_id", "subject", "predicate", "object_id", "object",
              "subject_type", "object_type", "family", "paper_id", "evidence_line", "evidence",
              "evidence_text_match", "direction_ok", "polarity", "modality", "review_status", "source"]


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #
def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def paper_title(md_path: Path) -> str:
    try:
        with open(md_path, encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("# "):
                    return line[2:].strip()
    except OSError:
        pass
    return md_path.stem


def short(text: str, limit: int = 260) -> str:
    value = " ".join(str(text or "").split())
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def clean_line(text: str) -> str:
    return short(clean_text(text), 240)


def search_key(text: str | None) -> str:
    """Lookup key that keeps CJK characters (the v3 normalize_key drops them)."""
    value = clean_text(text or "").lower()
    return re.sub(r"[^a-z0-9\u3400-\u9fff]+", "", value)


# --------------------------------------------------------------------------- #
# load + validate
# --------------------------------------------------------------------------- #
def load_graph(input_dir: Path) -> dict:
    concepts = read_jsonl(input_dir / "concepts.jsonl")
    instances = read_jsonl(input_dir / "instances.jsonl")
    relations = read_jsonl(input_dir / "relations.jsonl")
    observations = read_jsonl(input_dir / "observations.jsonl")
    stats_path = input_dir / "stats.json"
    stats = json.loads(stats_path.read_text(encoding="utf-8")) if stats_path.exists() else {}
    manifest_path = input_dir / "manifest.json"
    input_manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}

    problems: list[str] = []
    if len({concept["concept_id"] for concept in concepts}) != len(concepts):
        problems.append("duplicate concept_id in concepts.jsonl")
    if len({instance["instance_id"] for instance in instances}) != len(instances):
        problems.append("duplicate instance_id in instances.jsonl")

    node_ids = {concept["concept_id"] for concept in concepts}
    node_ids |= {instance["instance_id"] for instance in instances}
    seen_relations: set[str] = set()
    missing_endpoints = 0
    for relation in relations:
        rid = relation.get("relation_id")
        if not rid or rid in seen_relations:
            problems.append(f"duplicate or empty relation_id: {rid!r}")
        seen_relations.add(rid)
        if relation.get("subject_id") not in node_ids:
            missing_endpoints += 1
        if relation.get("object_id") not in node_ids:
            missing_endpoints += 1
    if missing_endpoints:
        problems.append(f"{missing_endpoints} relation endpoints missing from the node layer")

    for instance in instances:
        # a paper-scoped instance must carry its own paper
        if not instance.get("paper_id"):
            problems.append(f"instance without paper scope: {instance.get('instance_id')}")

    if problems:
        raise SystemExit("input validation failed:\n  - " + "\n  - ".join(problems[:20]))
    return {"concepts": concepts, "instances": instances, "relations": relations,
            "observations": observations, "stats": stats, "input_manifest": input_manifest}


# --------------------------------------------------------------------------- #
# nodes and deterministic layout
# --------------------------------------------------------------------------- #
def build_nodes(graph: dict) -> tuple[list[dict], dict[str, int]]:
    nodes: list[dict] = []
    index: dict[str, int] = {}
    for concept in graph["concepts"]:
        index[concept["concept_id"]] = len(nodes)
        nodes.append({
            "node_id": concept["concept_id"],
            "kind": "concept",
            "label": concept["canonical_name"],
            "type": concept.get("type") or "material",
            "quality": concept.get("quality") or "clean",
            "paper_count": int(concept.get("paper_count") or 0),
            "mention_count": int(concept.get("mention_count") or 0),
            "papers": concept.get("papers") or [],
            "aliases": [alias.get("alias") for alias in concept.get("aliases") or [] if alias.get("alias")],
            "surface_forms": list(concept.get("surface_forms") or {}),
            "zh": (concept.get("language_labels") or {}).get("zh_suggested"),
            "formula": concept.get("formula"),
            "linked_concept_id": None,
            "community": -1,
            "degree": 0,
            "in_graph": False,
            "x": 0.0, "y": 0.0,
        })
    for instance in graph["instances"]:
        index[instance["instance_id"]] = len(nodes)
        nodes.append({
            "node_id": instance["instance_id"],
            "kind": "instance",
            "label": instance.get("label") or instance["instance_id"],
            "type": "sample",
            "quality": "clean",
            "paper_count": 1,
            "mention_count": 1,
            "papers": [instance.get("paper_id")],
            "aliases": [],
            "surface_forms": [instance.get("label") or ""],
            "zh": None,
            "formula": None,
            "linked_concept_id": instance.get("linked_concept_id"),
            "community": -1,
            "degree": 0,
            "in_graph": False,
            "x": 0.0, "y": 0.0,
        })
    degree: Counter = Counter()
    for relation in graph["relations"]:
        degree[relation["subject_id"]] += 1
        degree[relation["object_id"]] += 1
    for node in nodes:
        node["degree"] = degree.get(node["node_id"], 0)
        node["in_graph"] = node["degree"] > 0
    return nodes, index


COMMUNITY_COLORS = [
    "#4e79a7", "#59a14f", "#f28e2b", "#b07aa1", "#e15759", "#76b7b2",
    "#edc948", "#ff9da7", "#9c755f", "#8c8c8c", "#7c9b3f", "#af7aa1",
    "#499894", "#d37295", "#a0cbe8", "#8cd17d", "#f1ce63", "#d4a6c8",
    "#86bcb6", "#fabfd2", "#b6992d", "#79706e", "#bcbd22", "#17becf",
]


def detect_communities(adjacency: list[list[int]], count: int, seed: int = 7) -> list[int]:
    """Louvain communities over the relation graph (falls back to label propagation)."""
    try:
        import networkx as nx

        graph = nx.Graph()
        graph.add_nodes_from(range(count))
        for vertex, neighbours in enumerate(adjacency):
            for neighbour in neighbours:
                if vertex < neighbour:
                    graph.add_edge(vertex, neighbour)
        parts = [set(part) for part in nx.community.louvain_communities(graph, seed=seed, resolution=1.15)]
        # Louvain keeps the giant connected component together; split it recursively so the
        # map has readable blobs instead of one mega-cluster.
        queue = list(parts)
        parts = []
        while queue:
            members = queue.pop()
            if len(members) <= 1200:
                parts.append(members)
                continue
            subgraph = graph.subgraph(members)
            subs = [set(part) for part in nx.community.louvain_communities(subgraph, seed=seed, resolution=3.0)]
            if len(subs) <= 1:
                parts.append(members)
            else:
                queue.extend(subs)
        labels = list(range(count))
        for community_id, members in enumerate(parts):
            for member in members:
                labels[member] = community_id
        return labels
    except Exception:  # networkx missing or too slow: deterministic label propagation
        labels = list(range(count))
        rng = np.random.default_rng(seed)
        for _ in range(8):
            for vertex in rng.permutation(count):
                neighbours = adjacency[vertex]
                if not neighbours:
                    continue
                votes: Counter = Counter(labels[neighbour] for neighbour in neighbours)
                best = max(votes.items(), key=lambda item: (item[1], -item[0]))[0]
                labels[vertex] = best
        return labels


def layout_communities(nodes: list[dict], node_index: dict[str, int],
                       relations: list[dict]) -> dict:
    """Type-region map: labelled type discs filled with community patches.

    Every relation node gets a deterministic position. Louvain communities form small
    sub-blobs inside their type disc, so the map reads as coloured patches inside labelled
    regions instead of a dense grid.
    """
    count = len(nodes)
    adjacency: list[list[int]] = [[] for _ in range(count)]
    for relation in relations:
        subject = node_index[relation["subject_id"]]
        obj = node_index[relation["object_id"]]
        adjacency[subject].append(obj)
        adjacency[obj].append(subject)

    raw_labels = detect_communities(adjacency, count)
    community_sizes = Counter(label for index, label in enumerate(raw_labels)
                              if nodes[index]["in_graph"])
    ordered_labels = [label for label, _ in community_sizes.most_common()]
    compact = {label: position for position, label in enumerate(ordered_labels)}

    node_community = [-1] * count
    for index in range(count):
        if nodes[index]["in_graph"]:
            node_community[index] = compact[raw_labels[index]]
            nodes[index]["community"] = node_community[index]

    by_type: dict[str, list[int]] = defaultdict(list)
    for index, node in enumerate(nodes):
        if node["in_graph"]:
            by_type[node["type"]].append(index)
    types = sorted(by_type, key=lambda item: -len(by_type[item]))
    region_radius = {node_type: 19.5 * math.sqrt(len(by_type[node_type])) + 60.0
                     for node_type in types}

    # deterministic sunflower packing of the type discs, then a short overlap relaxation
    total = len(types)
    golden_pack = math.pi * (3 - math.sqrt(5))
    centers = np.zeros((total, 2))
    placed: list[int] = []
    for rank, type_index in enumerate(sorted(range(total),
                                             key=lambda i: -region_radius[types[i]])):
        if not placed:
            centers[type_index] = (0.0, 0.0)
            placed.append(type_index)
            continue
        angle = rank * golden_pack
        direction = np.array([math.cos(angle), math.sin(angle)])
        distance = 0.0
        candidate = np.array([0.0, 0.0])
        for _ in range(500):
            distance += 45.0
            candidate = direction * distance
            if all(math.hypot(*(candidate - centers[other])) >=
                   region_radius[types[type_index]] + region_radius[types[other]] + 120
                   for other in placed):
                break
        centers[type_index] = candidate
        placed.append(type_index)
    radius_array = np.array([region_radius[node_type] for node_type in types])
    for _ in range(80):
        delta = centers[:, None, :] - centers[None, :, :]
        distance = np.sqrt((delta ** 2).sum(-1)) + 1e-6
        overlap = np.maximum(0.0, radius_array[:, None] + radius_array[None, :] + 120 - distance)
        np.fill_diagonal(overlap, 0.0)
        if overlap.max() < 0.5:
            break
        centers += (delta / distance[..., None] * (overlap / distance)[..., None]).sum(1) * 0.5
    centers -= centers.mean(0)

    golden = math.pi * (3 - math.sqrt(5))
    patches: list[dict] = []
    for type_index, node_type in enumerate(types):
        members = by_type[node_type]
        center_x, center_y = float(centers[type_index][0]), float(centers[type_index][1])
        disc_radius = region_radius[node_type] * 0.92

        groups: dict[int, list[int]] = defaultdict(list)
        for index in members:
            groups[node_community[index]].append(index)
        group_list = sorted(groups.values(), key=len, reverse=True)
        if len(group_list) > 11:
            rest = [index for group in group_list[11:] for index in group]
            group_list = group_list[:11] + ([rest] if rest else [])
        group_list.sort(key=len, reverse=True)
        group_count = len(group_list)
        for group_position, group in enumerate(group_list):
            group.sort(key=lambda index: (-nodes[index]["degree"], nodes[index]["node_id"]))
            if group_count == 1:
                group_x, group_y, group_radius = center_x, center_y, disc_radius
            else:
                ring = disc_radius * 0.62 * math.sqrt((group_position + 0.5) / group_count)
                theta = group_position * golden
                group_x = center_x + ring * math.cos(theta)
                group_y = center_y + ring * math.sin(theta)
                group_radius = disc_radius * 0.82 * math.sqrt(len(group) / max(1, len(members)))
            group_radius = max(group_radius, 20.0)
            if len(group) >= 30:
                patches.append({
                    "type": node_type,
                    "size": len(group),
                    "label": nodes[group[0]]["label"],
                    "color": COMMUNITY_COLORS[node_community[group[0]] % len(COMMUNITY_COLORS)],
                    "cx": round(group_x, 2),
                    "cy": round(group_y, 2),
                    "r": round(group_radius, 2),
                })
            for position, index in enumerate(group):
                r = group_radius * math.sqrt((position + 0.5) / max(1, len(group)))
                theta = position * golden
                nodes[index]["x"] = round(group_x + r * math.cos(theta), 2)
                nodes[index]["y"] = round(group_y + r * math.sin(theta), 2)

    in_graph = [index for index in range(count) if nodes[index]["in_graph"]]
    min_x = min(nodes[index]["x"] for index in in_graph)
    min_y = min(nodes[index]["y"] for index in in_graph)
    max_x = max(nodes[index]["x"] for index in in_graph)
    max_y = max(nodes[index]["y"] for index in in_graph)

    members_by_community: dict[int, list[int]] = defaultdict(list)
    for index in in_graph:
        members_by_community[node_community[index]].append(index)
    community_rows = []
    for community_id in range(min(60, len(ordered_labels))):
        members = members_by_community.get(community_id, [])
        if not members:
            continue
        center_x = sum(nodes[index]["x"] for index in members) / len(members)
        center_y = sum(nodes[index]["y"] for index in members) / len(members)
        top = sorted(members, key=lambda index: (-nodes[index]["degree"], nodes[index]["node_id"]))[:5]
        community_rows.append({
            "id": community_id,
            "size": len(members),
            "label": nodes[top[0]]["label"] if top else f"community {community_id}",
            "type": nodes[top[0]]["type"] if top else "material",
            "color": COMMUNITY_COLORS[community_id % len(COMMUNITY_COLORS)],
            "cx": round(center_x, 2),
            "cy": round(center_y, 2),
            "r": round(19.5 * math.sqrt(len(members)) + 20, 2),
            "top": [int(index) for index in top],
        })

    region_rows = []
    for type_index, node_type in enumerate(types):
        region_rows.append({
            "type": node_type,
            "count": len(by_type[node_type]),
            "label_zh": TYPE_LABELS.get(node_type, node_type),
            "label_en": TYPE_LABELS_EN.get(node_type, node_type),
            "color": TYPE_COLORS.get(node_type, "#888888"),
            "cx": round(float(centers[type_index][0]), 2),
            "cy": round(float(centers[type_index][1]), 2),
            "r": round(region_radius[node_type], 2),
        })

    for node in nodes:
        if not node["in_graph"]:
            node["x"] = -1.0
            node["y"] = -1.0
    extent = [round(max_x - min_x, 2), round(max_y - min_y, 2)]
    return {"communities": community_rows, "regions": region_rows, "patches": patches,
            "node_community": node_community, "extent": extent}


# --------------------------------------------------------------------------- #
# search index
# --------------------------------------------------------------------------- #
def build_search_index(nodes: list[dict]) -> dict:
    """Normalised key -> node indices. Case folding is for candidate lookup only."""
    keys: dict[str, list[int]] = defaultdict(list)

    def add(label: str | None, index: int) -> None:
        if not label:
            return
        key = search_key(label)
        if len(key) < 2:
            return
        bucket = keys[key]
        if index not in bucket and len(bucket) < 12:
            bucket.append(index)

    for position, node in enumerate(nodes):
        add(node["label"], position)
        for alias in node["aliases"]:
            add(alias, position)
        for surface in node["surface_forms"][:6]:
            if surface and len(surface) <= 70:
                add(surface, position)
        add(node["zh"], position)
    return {"k": dict(keys)}


# --------------------------------------------------------------------------- #
# evidence shards
# --------------------------------------------------------------------------- #
def build_evidence(graph: dict, nodes_index: dict[str, int], papers_dir: Path,
                   output_dir: Path, bundle_papers: bool) -> tuple[dict[str, dict], dict[str, str]]:
    """One JSON shard per paper with the evidence text and its markdown context."""
    by_paper: dict[str, list[dict]] = defaultdict(list)
    for relation in graph["relations"]:
        by_paper[relation["paper_id"]].append(relation)

    md_paths: dict[str, Path] = {}
    for md in sorted(papers_dir.glob("*.md")):
        md_paths[md.stem] = md
    missing_md = [paper for paper in by_paper if paper not in md_paths]

    line_cache: dict[str, list[str]] = {}
    papers_meta: dict[str, str] = {}
    shards: dict[str, dict] = {}
    if bundle_papers:
        (output_dir / "papers").mkdir(parents=True, exist_ok=True)
    for paper, relations in by_paper.items():
        md = md_paths.get(paper)
        title = paper_title(md) if md else paper
        lines = []
        if md:
            lines = md.read_text(encoding="utf-8").splitlines()
            line_cache[paper] = lines
        link_rel = ""
        if bundle_papers and md:
            target = output_dir / "papers" / f"{paper}.md"
            target.write_text(md.read_text(encoding="utf-8"), encoding="utf-8")
            link_rel = f"papers/{paper}.md"
        elif md:
            link_rel = os.path.relpath(md, output_dir).replace("\\", "/")
        papers_meta[paper] = {"title": title, "md": link_rel}
        shard: dict[str, list] = {}
        for relation in relations:
            line = relation.get("evidence_line")
            context = ""
            if isinstance(line, int) and lines and 1 <= line <= len(lines):
                window = lines[max(0, line - 2): min(len(lines), line + 1)]
                context = " / ".join(clean_line(item) for item in window if item.strip())[:360]
            shard[relation["relation_id"]] = [short(relation.get("evidence"), 300),
                                              line if isinstance(line, int) else None,
                                              context]
        shards[paper] = shard
    if missing_md:
        print(f"warning: {len(missing_md)} papers have no markdown file (evidence text only)")
    return shards, papers_meta


# --------------------------------------------------------------------------- #
# overview aggregates
# --------------------------------------------------------------------------- #
def build_overview(graph: dict, nodes: list[dict], node_index: dict[str, int]) -> dict:
    in_graph = [node for node in nodes if node["in_graph"]]
    type_counts = Counter(node["type"] for node in in_graph)
    type_edges: Counter = Counter()
    for relation in graph["relations"]:
        s_type = nodes[node_index[relation["subject_id"]]]["type"]
        o_type = nodes[node_index[relation["object_id"]]]["type"]
        type_edges[(s_type, o_type)] += 1
    representatives: dict[str, list[int]] = {}
    by_type: dict[str, list[int]] = defaultdict(list)
    for position, node in enumerate(nodes):
        if node["in_graph"]:
            by_type[node["type"]].append(position)
    for node_type, positions in by_type.items():
        positions.sort(key=lambda p: (-nodes[p]["degree"], nodes[p]["label"]))
        representatives[node_type] = positions[:6]
    # circle positions for the summary view
    types = [t for t in TYPE_ORDER if type_counts.get(t)] + [t for t in type_counts if t not in TYPE_ORDER]
    radius = 430.0
    centers = {}
    for position, node_type in enumerate(types):
        angle = 2 * math.pi * position / max(1, len(types)) - math.pi / 2
        centers[node_type] = [round(math.cos(angle) * radius, 2), round(math.sin(angle) * radius, 2)]
    return {
        "types": [{"type": t, "count": type_counts[t], "label": TYPE_LABELS.get(t, t),
                   "color": TYPE_COLORS.get(t, "#888888"), "x": centers[t][0], "y": centers[t][1]}
                  for t in types],
        "edges": [{"s": s, "o": o, "count": count} for (s, o), count in
                  sorted(type_edges.items(), key=lambda item: -item[1]) if s != o],
        "self_edges": [{"s": s, "count": count} for (s, o), count in
                       sorted(type_edges.items(), key=lambda item: -item[1]) if s == o],
        "representatives": representatives,
    }


# --------------------------------------------------------------------------- #
# writers
# --------------------------------------------------------------------------- #
def write_triples(package: dict, output_dir: Path) -> None:
    rows = package["triples"]
    with open(output_dir / "triples_full.csv", "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: ("" if row.get(key) is None else row.get(key)) for key in CSV_FIELDS})
    with open(output_dir / "triples_full.jsonl", "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    with open(output_dir / "nodes.jsonl", "w", encoding="utf-8") as handle:
        for node in package["nodes"]:
            handle.write(json.dumps(node, ensure_ascii=False) + "\n")


def build_triples(graph: dict, nodes: list[dict], node_index: dict[str, int]) -> list[dict]:
    triples = []
    for relation in graph["relations"]:
        subject = nodes[node_index[relation["subject_id"]]]
        obj = nodes[node_index[relation["object_id"]]]
        triples.append({
            "relation_id": relation["relation_id"],
            "subject_id": relation["subject_id"],
            "subject": relation["subject_label"],
            "predicate": relation["predicate"],
            "object_id": relation["object_id"],
            "object": relation["object_label"],
            "subject_type": relation["subject_type"],
            "object_type": relation["object_type"],
            "family": relation.get("family"),
            "paper_id": relation["paper_id"],
            "evidence_line": relation.get("evidence_line"),
            "evidence": relation.get("evidence"),
            "evidence_text_match": relation.get("evidence_text_match"),
            "direction_ok": bool(relation.get("direction_ok")),
            "polarity": relation.get("polarity"),
            "modality": relation.get("modality"),
            "review_status": relation.get("review_status"),
            "source": relation.get("source"),
            "duplicate_count": relation.get("duplicate_count", 1),
            "subject_kind": subject["kind"],
            "object_kind": obj["kind"],
        })
    triples.sort(key=lambda row: (row["paper_id"], row["relation_id"]))
    return triples


def write_browser_data(graph: dict, nodes: list[dict], node_index: dict[str, int],
                       triples: list[dict], overview: dict, shards: dict[str, dict],
                       papers_meta: dict[str, dict], output_dir: Path, version: str) -> dict:
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    type_ids = {t: i for i, t in enumerate(TYPE_ORDER)}
    predicates = sorted({row["predicate"] for row in triples})
    predicate_ids = {p: i for i, p in enumerate(predicates)}
    families = sorted({row["family"] or "other" for row in triples})
    family_ids = {f: i for i, f in enumerate(families)}
    paper_ids = sorted({row["paper_id"] for row in triples})
    paper_index = {p: i for i, p in enumerate(paper_ids)}

    node_rows = []
    for node in nodes:
        node_rows.append([
            node["node_id"], node["label"], type_ids.get(node["type"], len(type_ids)),
            node["quality"], node["paper_count"], node["mention_count"], node["degree"],
            1 if node["in_graph"] else 0, node["x"], node["y"],
            node["community"], node["zh"] or None,
            node["aliases"][:12],
            node["surface_forms"][:12],
            node["papers"][0] if node["kind"] == "instance" and node["papers"] else None,
        ])

    rel_index = {row["relation_id"]: i for i, row in enumerate(triples)}
    edge_rows = []
    adjacency: dict[int, list[list[int]]] = defaultdict(list)
    for row in triples:
        s_idx = node_index[row["subject_id"]]
        o_idx = node_index[row["object_id"]]
        flags = 0
        if not row["direction_ok"]:
            flags |= 1
        if row["evidence_line"] in (None, ""):
            flags |= 2
        position = rel_index[row["relation_id"]]
        edge_rows.append([position, s_idx, o_idx, predicate_ids[row["predicate"]],
                          family_ids[row["family"] or "other"], paper_index[row["paper_id"]], flags])
        adjacency[s_idx].append([position, o_idx, 1])
        adjacency[o_idx].append([position, s_idx, -1])

    meta = {
        "package": "materials_kg",
        "version": version,
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "papers": len(paper_ids),
        "concepts": sum(1 for node in nodes if node["kind"] == "concept"),
        "instances": sum(1 for node in nodes if node["kind"] == "instance"),
        "relations": len(triples),
        "in_graph_nodes": sum(1 for node in nodes if node["in_graph"]),
        "searchable_only_nodes": sum(1 for node in nodes if not node["in_graph"]),
        "anomalies_direction": sum(1 for row in triples if not row["direction_ok"]),
        "no_evidence_line": sum(1 for row in triples if row["evidence_line"] in (None, "")),
        "types": [{"id": t, "label_zh": TYPE_LABELS.get(t, t),
                   "label_en": TYPE_LABELS_EN.get(t, t),
                   "color": TYPE_COLORS.get(t, "#888888")} for t in TYPE_ORDER],
        "families": [{"id": f, "label_zh": FAMILY_LABELS.get(f, f),
                        "label_en": FAMILY_LABELS_EN.get(f, f)} for f in families],
        "predicates": predicates,
        "paper_ids": paper_ids,
        "papers_meta": papers_meta,
    }

    write_json(data_dir / "meta.json", meta)
    write_json(data_dir / "nodes.json", node_rows)
    write_json(data_dir / "edges.json", edge_rows)
    write_json(data_dir / "relids.json", [row["relation_id"] for row in triples])
    write_json(data_dir / "adjacency.json", adjacency)
    write_json(data_dir / "overview.json", overview)
    search = build_search_index(nodes)
    write_json(data_dir / "search.json", search)

    evidence_dir = data_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for paper, shard in shards.items():
        safe = re.sub(r'[<>:"/\\|?*]', "_", paper)
        write_json(evidence_dir / f"{safe}.json", shard)
    write_json(data_dir / "papers.json", {"papers": paper_ids, "meta": papers_meta})
    return {"predicates": predicates, "families": families, "papers": paper_ids,
            "search_keys": len(search["k"]), "edge_rows": len(edge_rows)}


# --------------------------------------------------------------------------- #
# overview figure (Pillow; same data and layout as the page's summary view)
# --------------------------------------------------------------------------- #
def render_overview_png(overview: dict, meta: dict, nodes: list[dict], path: Path,
                        size: tuple[int, int] = (2600, 1600)) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("warning: Pillow not available; overview PNG not rendered")
        return

    width, height = size
    image = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(image)
    font_path = Path("C:/Windows/Fonts/msyh.ttc")
    bold_path = Path("C:/Windows/Fonts/msyhbd.ttc")

    def font(px: int, bold: bool = False):
        try:
            return ImageFont.truetype(str(bold_path if bold and bold_path.exists() else font_path), px)
        except OSError:
            return ImageFont.load_default()

    draw.text((70, 52), "材料专业术语知识图谱 · 全库总览", fill="#1a1a1a", font=font(52, True))
    draw.text((70, 122),
              f"{meta['papers']} 篇论文 · {meta['relations']:,} 条规范关系 · "
              f"{meta['concepts']:,} 个专业概念 · {meta['instances']:,} 个论文内实例 · "
              f"{meta['in_graph_nodes']:,} 个关系节点",
              fill="#555555", font=font(25))
    draw.text((70, 160),
              "类型间连线粗细 = 规范关系数量；节点内数字 = 被关系引用的该类型节点数；"
              "另有 %s 个暂无关系的概念/实例可检索但不占位。" % f"{meta['searchable_only_nodes']:,}",
              fill="#777777", font=font(20))

    cx, cy, radius = width / 2, height / 2 + 60, 430
    type_nodes = overview["types"]
    positions = {}
    for item in type_nodes:
        x = cx + item["x"] * radius / 430
        y = cy + item["y"] * radius / 430
        positions[item["type"]] = (x, y)

    max_count = max((edge["count"] for edge in overview["edges"]), default=1)
    for edge in overview["edges"]:
        start, end = positions.get(edge["s"]), positions.get(edge["o"])
        if not start or not end:
            continue
        width_line = 1 + 7 * math.sqrt(edge["count"] / max_count)
        draw.line([start, end], fill="#c9c9c9", width=int(width_line))
    for edge in overview["self_edges"]:
        point = positions.get(edge["s"])
        if not point:
            continue
        draw.arc([point[0] - 36, point[1] - 36, point[0] + 36, point[1] + 36], 0, 300,
                 fill="#d0d0d0", width=2)

    for item in type_nodes:
        x, y = positions[item["type"]]
        count = item["count"]
        r = 34 + math.sqrt(count) * 1.55
        draw.ellipse([x - r, y - r, x + r, y + r], fill=item["color"], outline="#ffffff", width=3)
        text = item["label"]
        count_text = f"{count:,}"
        draw.text((x, y - 12), text, fill="#ffffff", font=font(24, True), anchor="mm")
        draw.text((x, y + 16), count_text, fill="#ffffff", font=font(19), anchor="mm")

    # representative terms per type in a band on the right
    x0, y0 = 70, height - 360
    draw.text((70, y0 - 42), "代表术语（按关系数）", fill="#333333", font=font(24, True))
    column_width = (width - 140) / 3
    for i, item in enumerate(type_nodes):
        reps = [nodes[idx]["label"] for idx in overview["representatives"].get(item["type"], [])[:3]]
        col, row = i % 3, i // 3
        line_y = y0 + row * 26
        text = f"{item['label']}：" + "、".join(reps)
        draw.text((70 + col * column_width, line_y), short(text, 60), fill="#444444", font=font(17))

    draw.text((70, height - 44),
              "数据版本 %s · 生成 %s · 计数以 relation_id 为准，证据行号缺失 %s 条，方向待复核 %s 条"
              % (meta.get("version", "v3"), meta["generated"], f"{meta['no_evidence_line']:,}",
                 f"{meta['anomalies_direction']}"),
              fill="#888888", font=font(17))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG")
    print(f"overview figure: {path}")


# --------------------------------------------------------------------------- #
# static page
# --------------------------------------------------------------------------- #
def write_page(output_dir: Path) -> None:
    template = TEMPLATES / "materials_overview.html"
    js = TEMPLATES / "materials_overview.js"
    css = TEMPLATES / "materials_overview.css"
    for path in (template, js, css):
        if not path.exists():
            raise SystemExit(f"missing template: {path}")
    assets = output_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template, output_dir / "index.html")
    shutil.copyfile(js, assets / "app.js")
    shutil.copyfile(css, assets / "app.css")
    vendor = TEMPLATES / "vendor"
    for name in ("vis-network.min.js", "vis-network.min.css"):
        source = vendor / name
        if source.exists():
            shutil.copyfile(source, assets / name)
    if not (assets / "vis-network.min.js").exists():
        print("warning: vis-network vendor file missing; neighbourhood view will use canvas fallback")


def write_readme(output_dir: Path, manifest: dict) -> None:
    display_dir = output_dir.with_name(output_dir.name.replace(".staging", "").replace(".backup", ""))
    text = f"""# 材料专业术语知识图谱 · 交付包

版本：{manifest['version']}（数据版本 {manifest['data_version']}）
生成：{manifest['generated']}
规模：{manifest['papers']} 篇论文，{manifest['concepts']:,} 个概念，{manifest['instances']:,} 个论文内实例，
{manifest['relations']:,} 条规范关系（计数以 relation_id 为准）。

## 如何打开

```powershell
cd "{display_dir}"
python -m http.server 8766 --bind 127.0.0.1
```

浏览器打开 <http://127.0.0.1:8766/>。页面完全离线，不访问网络资源。

## 页面视图

1. **全库大图**（默认）：12 个类型区域，Louvain 社区显示为区域内的彩色斑块；区域标题、
   社区与枢纽术语标签；滚轮缩放、拖拽平移、悬停高亮邻居。
2. **全部关系**：当前筛选下的真实节点与关系画布（与全库大图同一渲染器）。
3. **类型汇总**：类型级汇总环图，点击类型进入该范围。
4. **术语邻域**：搜索或双击术语后的一跳邻域，可继续展开；点边看证据。

页面右上角的「EN / 中文」按钮切换界面语言（术语本身保持原文，中文建议标签另列）。
首页顶部显示「全库关系 / 当前筛选 / 当前已绘制」三个数字。筛选（类型、谓词族、论文、
方向异常）会同时作用于总数与画布。

## 文件说明

| 文件 | 内容 |
|---|---|
| `triples_full.csv` / `triples_full.jsonl` | 全部规范关系（CSV 带 UTF-8 BOM，可直接用 Excel 打开） |
| `nodes.jsonl` | 概念与论文内实例（含类型、质量、别名、坐标、度数） |
| `data/` | 页面用的简明数据、检索索引、邻接索引、按论文分片的证据 |
| `materials_kg_overview.png` | 全局汇报图（与页面总览同一数据与布局） |
| `manifest.json` | 输入版本、生成时间、计数、校验结果与主要文件 SHA-256 |
| `papers/` | （可选）论文 Markdown 原文，证据链接直接指向这里 |

## 计数口径

- **全库关系** = `relations.jsonl` 中唯一 `relation_id` 的数量（同一规范关系的多篇来源会保留，
  不因浏览器折叠而减少）。
- **当前筛选** = 应用类型/谓词族/论文/异常开关后的关系数。
- **当前已绘制** = 画布上已经画出的关系数（全图分批绘制，会逐步追上筛选数）。
- **方向异常** = `direction_ok=false` 的关系（{manifest['anomalies_direction']} 条），默认在邻域隐藏，
  可用开关显示；界面会标注“待复核”。
- **无行号证据** = {manifest['no_evidence_line']} 条，侧栏显示原文引文并标注“定位缺失”。

## 已知情况

- 概念类型由中心词规则统一，冲突记录见数据源 `type_conflicts.json`；本包按统一类型着色。
- 证据行号来自论文 Markdown 快照；原文变动时行号需重新核对。
- 本包为交付验收：全量守恒、端点完整、定位案例可核对；不代表全库证据语义准确率或召回率。
"""
    stats = manifest.get("input_stats") or {}
    stats = {key: (value if value is not None else 0) for key, value in stats.items()}
    if stats:
        text += f"""
## 本轮数据修复（来自输入层 {manifest['data_version']}）

- 观测字段：{stats.get('observations', 0):,} 条观测中，{stats.get('observations_with_value', 0):,} 条恢复数值，
  {stats.get('observations_with_unit', 0):,} 条恢复单位，{stats.get('observations_with_sample_id', 0):,} 条恢复样品 ID，
  {stats.get('observations_with_conditions', 0):,} 条恢复条件（共 {stats.get('observation_condition_pairs', 0):,} 个条件项）。
  数值与条件只放在观测/样品侧栏，不作为跨论文性能排名使用。
- 术语补抽：从 12 个定向补抽文件读入 {stats.get('terms_accepted', 0) + stats.get('terms_merged', 0) + stats.get('terms_rejected', 0):,}
  个术语条目，接受 {stats.get('terms_accepted', 0):,}、并入既有概念 {stats.get('terms_merged', 0):,}、
  拒绝 {stats.get('terms_rejected', 0):,}（拒绝原因见数据源 `term_ingest_log.json`）。
- 仍待处理：{stats.get('type_conflicts', 0):,} 条类型冲突、{stats.get('direction_flagged', 0)} 条方向待复核、
  {manifest['no_evidence_line']:,} 条证据无行号；全库误合并审计与剩余概念粒度问题留待下一轮。
"""
    (output_dir / "README_打开方式.md").write_text(text, encoding="utf-8")


# --------------------------------------------------------------------------- #
# export
# --------------------------------------------------------------------------- #
def export(input_dir: Path, papers_dir: Path, output_dir: Path, version: str,
           bundle_papers: bool, gexf: bool) -> dict:
    graph = load_graph(input_dir)
    nodes, node_index = build_nodes(graph)
    layout = layout_communities(nodes, node_index, graph["relations"])
    triples = build_triples(graph, nodes, node_index)
    overview = build_overview(graph, nodes, node_index)
    shards, papers_meta = build_evidence(graph, node_index, papers_dir, output_dir, bundle_papers)

    output_dir.mkdir(parents=True, exist_ok=True)
    package = {"triples": triples, "nodes": nodes}
    write_triples(package, output_dir)
    (output_dir / "data").mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "data" / "communities.json",
               {"count": len(layout["communities"]), "extent": list(layout["extent"]),
                "list": layout["communities"], "regions": layout["regions"],
                "patches": layout["patches"]})
    extra = write_browser_data(graph, nodes, node_index, triples, overview, shards,
                               papers_meta, output_dir, version)
    write_page(output_dir)

    meta_for_png = {
        "papers": len(extra["papers"]),
        "relations": len(triples),
        "concepts": sum(1 for node in nodes if node["kind"] == "concept"),
        "instances": sum(1 for node in nodes if node["kind"] == "instance"),
        "in_graph_nodes": sum(1 for node in nodes if node["in_graph"]),
        "searchable_only_nodes": sum(1 for node in nodes if not node["in_graph"]),
        "anomalies_direction": sum(1 for row in triples if not row["direction_ok"]),
        "no_evidence_line": sum(1 for row in triples if row["evidence_line"] in (None, "")),
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": version,
    }
    render_overview_png(overview, meta_for_png, nodes, output_dir / "materials_kg_overview.png")

    if gexf:
        write_gexf(triples, nodes, node_index, output_dir / "materials_kg.gexf")

    files = ["triples_full.csv", "triples_full.jsonl", "nodes.jsonl", "index.html",
             "data/communities.json",
             "assets/app.js", "assets/app.css", "data/meta.json", "data/nodes.json",
             "data/edges.json", "data/relids.json", "data/adjacency.json", "data/overview.json",
             "data/search.json", "materials_kg_overview.png"]
    manifest = {
        "package": "materials_kg",
        "version": version,
        "data_version": graph["stats"].get("version", "v3"),
        "input_dir": str(input_dir),
        "papers_dir": str(papers_dir),
        "generated": meta_for_png["generated"],
        "papers": meta_for_png["papers"],
        "concepts": meta_for_png["concepts"],
        "instances": meta_for_png["instances"],
        "relations": meta_for_png["relations"],
        "unique_relation_ids": len({row["relation_id"] for row in triples}),
        "in_graph_nodes": meta_for_png["in_graph_nodes"],
        "searchable_only_nodes": meta_for_png["searchable_only_nodes"],
        "missing_endpoints": 0,
        "csv_rows": len(triples),
        "anomalies_direction": meta_for_png["anomalies_direction"],
        "no_evidence_line": meta_for_png["no_evidence_line"],
        "evidence_shards": len(shards),
        "search_keys": extra["search_keys"],
        "bundle_papers": bundle_papers,
        "input_stats": {key: graph["stats"].get(key) for key in (
            "observations", "observations_with_value", "observations_with_unit",
            "observations_with_sample_id", "observations_with_conditions",
            "observation_condition_pairs", "observations_unmatched_owner",
            "terms_accepted", "terms_merged", "terms_rejected",
            "type_conflicts", "direction_flagged")},
        "files": {name: sha256(output_dir / name) for name in files if (output_dir / name).exists()},
        "notes": [
            "counts use relation_id as the unit",
            "paper-scoped instances keep their paper_id and are never merged across papers",
            "evidence shards are loaded on demand; the page itself needs no network",
        ],
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                                              encoding="utf-8")
    write_readme(output_dir, manifest)
    return manifest


def write_gexf(triples: list[dict], nodes: list[dict], node_index: dict[str, int], path: Path) -> None:
    used = {row["subject_id"] for row in triples} | {row["object_id"] for row in triples}
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<gexf xmlns="http://www.gexf.net/1.2draft" version="1.2">',
             f'<meta><creator>materials_kg</creator><description>{len(triples)} relations</description></meta>',
             '<graph mode="static" defaultedgetype="directed">', "<nodes>"]
    for node_id in sorted(used):
        node = nodes[node_index[node_id]]
        label = (node["label"] or node_id).replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")
        lines.append(f'<node id="{node_id}" label="{label}"><attvalues>'
                     f'<attvalue for="type" value="{node["type"]}"/></attvalues></node>')
    lines.append("</nodes><edges>")
    for position, row in enumerate(triples):
        lines.append(f'<edge id="{position}" source="{row["subject_id"]}" target="{row["object_id"]}" '
                     f'label="{row["predicate"].replace("&", "&amp;").replace(chr(34), "&quot;")}"/>')
    lines.append("</edges></graph></gexf>")
    path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------- #
# verification
# --------------------------------------------------------------------------- #
def verify(output_dir: Path) -> bool:
    manifest_path = output_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"FAIL: manifest.json missing in {output_dir}")
        return False
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, ok, detail))

    required = ["index.html", "assets/app.js", "assets/app.css", "triples_full.csv",
                "triples_full.jsonl", "nodes.jsonl", "materials_kg_overview.png",
                "README_打开方式.md", "data/meta.json", "data/nodes.json", "data/edges.json",
                "data/overview.json", "data/search.json"]
    missing = [name for name in required if not (output_dir / name).exists()]
    check("required files present", not missing, ", ".join(missing))

    csv_rows = 0
    with open(output_dir / "triples_full.csv", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        for _ in reader:
            csv_rows += 1
    check("csv columns", all(field in headers for field in CSV_FIELDS),
          f"{len(headers)} columns")
    check("csv rows == manifest relations", csv_rows == manifest["relations"],
          f"csv={csv_rows} manifest={manifest['relations']}")

    triple_ids: set[str] = set()
    jsonl_rows = 0
    with open(output_dir / "triples_full.jsonl", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            triple_ids.add(row["relation_id"])
            jsonl_rows += 1
    check("jsonl rows == manifest relations", jsonl_rows == manifest["relations"],
          f"jsonl={jsonl_rows}")
    check("unique relation ids == jsonl rows", len(triple_ids) == jsonl_rows,
          f"unique={len(triple_ids)}")

    node_ids: set[str] = set()
    node_rows = 0
    with open(output_dir / "nodes.jsonl", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                node = json.loads(line)
                node_ids.add(node["node_id"])
                node_rows += 1
    check("node count", node_rows == manifest["concepts"] + manifest["instances"],
          f"nodes={node_rows}")

    missing_endpoints = 0
    papers: set[str] = set()
    with open(output_dir / "triples_full.jsonl", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            papers.add(row["paper_id"])
            if row["subject_id"] not in node_ids or row["object_id"] not in node_ids:
                missing_endpoints += 1
    check("endpoints resolvable", missing_endpoints == 0, f"missing={missing_endpoints}")
    check("papers covered", len(papers) == manifest["papers"],
          f"papers={len(papers)} manifest={manifest['papers']}")

    shards = list((output_dir / "data" / "evidence").glob("*.json"))
    check("evidence shards", len(shards) == manifest["evidence_shards"],
          f"shards={len(shards)}")

    # term / alias lookup acceptance (the four terms the plan names, plus Chinese)
    nodes_path = output_dir / "data" / "nodes.json"
    search_path = output_dir / "data" / "search.json"
    if nodes_path.exists() and search_path.exists():
        nodes = json.loads(nodes_path.read_text(encoding="utf-8"))
        search = json.loads(search_path.read_text(encoding="utf-8")).get("k", {})

        def hit(key: str) -> list[dict]:
            return [nodes[index] for index in search.get(key, [])]

        def label_of(row: dict) -> str:
            return row[1]

        def names(row: dict) -> list[str]:
            return [row[1]] + list(row[12] or []) + list(row[13] or [])

        def has_term(key: str, needle: str, require_degree: bool = True) -> bool:
            for row in hit(key):
                if require_degree and not row[7]:
                    continue
                if any(needle.lower() in name.lower() for name in names(row)):
                    return True
            return False

        if manifest.get("relations", 0) < 1000:
            check("term lookup checks", True, "skipped: mini dataset (<1000 relations)")
        else:
            check("search ALD", has_term("ald", "atomic layer deposition"), "alias -> atomic layer deposition")
            check("search 4Cl-BZS", has_term("4clbzs", "4-chlorobenzenesulfonate"), "alias -> full ligand name")
            check("search AgBiS2", has_term("agbis2", "AgBiS2"), "formula")
            check("search 甲酸根", any(row[11] == "甲酸根" for row in hit("甲酸根")), "Chinese suggested label")
            alpha = {row[0] for row in hit("alphafapbi3")}
            delta = {row[0] for row in hit("deltafapbi3")}
            check("alpha/delta FAPbI3 stay separate", bool(alpha) and bool(delta) and not (alpha & delta),
                  f"alpha={len(alpha)} delta={len(delta)} shared={len(alpha & delta)}")

    hash_failures = []
    for name, expected in manifest.get("files", {}).items():
        path = output_dir / name
        if not path.exists() or sha256(path) != expected:
            hash_failures.append(name)
    check("file hashes match manifest", not hash_failures, ", ".join(hash_failures[:5]))

    print(f"verifying {output_dir}")
    for name, ok, detail in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" ({detail})" if detail else ""))
    passed = all(ok for _, ok, _ in checks)
    print(f"\n{sum(1 for _, ok, _ in checks if ok)}/{len(checks)} checks passed")
    return passed


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export the v3 graph as a delivery package")
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT), help="normalized v3 directory")
    parser.add_argument("--papers-dir", default=str(DEFAULT_PAPERS), help="markdown papers directory")
    parser.add_argument("--output-dir", default=str(ROOT / "delivery" / "materials_kg"),
                        help="package output directory")
    parser.add_argument("--version", default="", help="package version label (default: from input stats)")
    parser.add_argument("--verify-only", action="store_true", help="verify an existing package")
    parser.add_argument("--attach-png", default="", help="replace the overview PNG with this file")
    parser.add_argument("--bundle-papers", action="store_true", help="copy markdown papers into the package")
    parser.add_argument("--gexf", action="store_true", help="also export a GEXF file for Gephi")
    parser.add_argument("--force", action="store_true", help="overwrite an existing output directory")
    args = parser.parse_args(argv)

    input_dir = Path(args.input_dir).resolve()
    papers_dir = Path(args.papers_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    if args.verify_only:
        return 0 if verify(output_dir) else 1

    if args.attach_png:
        source = Path(args.attach_png).resolve()
        if not source.exists():
            print(f"attach-png: file not found {source}")
            return 2
        target = output_dir / "materials_kg_overview.png"
        shutil.copyfile(source, target)
        manifest_path = output_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest.setdefault("files", {})["materials_kg_overview.png"] = sha256(target)
        manifest["overview_png_source"] = "browser export"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"attached {source} -> {target}")
        return 0 if verify(output_dir) else 1

    if not input_dir.exists():
        print(f"input directory not found: {input_dir}")
        return 2
    if not papers_dir.exists():
        print(f"papers directory not found: {papers_dir}")
        return 2

    stats = {}
    if (input_dir / "stats.json").exists():
        stats = json.loads((input_dir / "stats.json").read_text(encoding="utf-8"))
    version = args.version or stats.get("version") or "v3"

    staging = output_dir.parent / (output_dir.name + ".staging")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    print(f"exporting {input_dir} -> {staging}")
    manifest = export(input_dir, papers_dir, staging, version, args.bundle_papers, args.gexf)
    if not verify(staging):
        print("verification failed; the staging directory was left in place for inspection")
        return 1

    if output_dir.exists():
        if not args.force:
            print(f"output directory exists: {output_dir}\n"
                  "use --force to replace it or choose a new --output-dir")
            shutil.rmtree(staging)
            return 2
        backup = output_dir.parent / (output_dir.name + ".backup")
        if backup.exists():
            shutil.rmtree(backup)
        output_dir.rename(backup)
        staging.rename(output_dir)
        shutil.rmtree(backup)
    else:
        staging.rename(output_dir)

    print(f"\npublished: {output_dir}")
    print(json.dumps({key: manifest[key] for key in
                      ("version", "papers", "concepts", "instances", "relations", "csv_rows",
                       "in_graph_nodes", "searchable_only_nodes", "anomalies_direction",
                       "no_evidence_line", "evidence_shards")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
