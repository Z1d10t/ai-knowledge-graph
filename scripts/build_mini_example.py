"""Build a tiny two-paper v3 example from the frozen delivery layer.

The example lets a fresh checkout run the export + verify pipeline without the 285-paper
corpus. It keeps only relations/observations of two papers, their concepts and their
paper Markdown files.
"""
from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path

PAPERS = [
    "029_Zhu_2021_A-flexible-ultrasensitive-optoelectronic-sensor",
    "088_Zhao_2022_Suppressing-ion-migration-in-metal-halide-perovs",
]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                    encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="evaluation/full_v3_delivery")
    parser.add_argument("--papers-dir", default="../材料论文/全部_285篇/md")
    parser.add_argument("--output", default="examples")
    args = parser.parse_args()

    source = Path(args.source)
    papers_dir = Path(args.papers_dir)
    output = Path(args.output)
    v3 = output / "mini_v3"
    mini_papers = output / "mini_papers"
    v3.mkdir(parents=True, exist_ok=True)
    mini_papers.mkdir(parents=True, exist_ok=True)

    wanted = set(PAPERS)
    relations = [row for row in read_jsonl(source / "relations.jsonl") if row["paper_id"] in wanted]
    observations = [row for row in read_jsonl(source / "observations.jsonl")
                    if row["paper_id"] in wanted]
    instances = [row for row in read_jsonl(source / "instances.jsonl") if row["paper_id"] in wanted]
    used_ids = {row["subject_id"] for row in relations} | {row["object_id"] for row in relations}
    used_ids |= {row["property_concept_id"] for row in observations}
    concepts = [row for row in read_jsonl(source / "concepts.jsonl") if row["concept_id"] in used_ids]

    write_jsonl(v3 / "relations.jsonl", relations)
    write_jsonl(v3 / "observations.jsonl", observations)
    write_jsonl(v3 / "instances.jsonl", instances)
    write_jsonl(v3 / "concepts.jsonl", concepts)
    write_jsonl(v3 / "numeric_facts.jsonl", [])
    write_jsonl(v3 / "mentions.jsonl", [])

    stats = {
        "version": "v3.0-mini",
        "papers": len(wanted),
        "concepts": len(concepts),
        "instances": len(instances),
        "relations": len(relations),
        "observations": len(observations),
        "relations_by_family": dict(Counter(row.get("family") for row in relations)),
        "direction_flagged": sum(1 for row in relations if not row.get("direction_ok", True)),
        "type_conflicts": 0,
    }
    (v3 / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8")
    (v3 / "manifest.json").write_text(json.dumps({
        "version": "v3.0-mini", "papers": len(wanted), "concepts": len(concepts),
        "instances": len(instances), "relations": len(relations),
        "note": "two-paper example generated from evaluation/full_v3_delivery",
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    for paper in PAPERS:
        source_md = papers_dir / f"{paper}.md"
        if source_md.exists():
            shutil.copy2(source_md, mini_papers / source_md.name)

    (output / "README.md").write_text(
        "# 两篇论文示例\n\n"
        "由 `scripts/build_mini_example.py` 从 `evaluation/full_v3_delivery` 截取，用于在没有全量数据时\n"
        "跑通导出与校验：\n\n"
        "```powershell\n"
        "python article/export_materials_graph.py --input-dir examples/mini_v3 "
        "--papers-dir examples/mini_papers --output-dir examples/mini_package --force\n"
        "python article/export_materials_graph.py --verify-only --output-dir examples/mini_package\n"
        "```\n",
        encoding="utf-8")
    print(json.dumps({"papers": len(wanted), "relations": len(relations),
                      "observations": len(observations), "concepts": len(concepts),
                      "instances": len(instances)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
