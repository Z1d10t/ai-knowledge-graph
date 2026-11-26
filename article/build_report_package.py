"""Build a compact progress-report package: figures + triples + summary statistics."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import statistics
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

FIELDS = ["relation_id", "subject_id", "subject", "predicate", "object_id", "object",
          "subject_type", "object_type", "family", "paper_id", "evidence_line", "evidence",
          "evidence_text_match", "direction_ok", "polarity", "modality", "review_status", "source"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_relations(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def pct(value: int, total: int) -> str:
    return f"{value / total * 100:.1f}%" if total else "0.0%"


def build(package: Path, screenshots: Path, output: Path, zip_path: Path) -> dict:
    manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
    meta = json.loads((package / "data" / "meta.json").read_text(encoding="utf-8"))
    relations = read_relations(package / "triples_full.csv")
    total = len(relations)

    figures = output / "图"
    triples_dir = output / "三元组"
    stats_dir = output / "统计"
    for folder in (figures, triples_dir, stats_dir):
        folder.mkdir(parents=True, exist_ok=True)

    figure_sources = [
        (package / "materials_kg_overview.png", figures / "01_知识图谱总览.png"),
        (screenshots / "01_全库大图.png", figures / "02_交互界面_全库大图.png"),
        (screenshots / "03_类型汇总.png", figures / "03_类型汇总.png"),
        (screenshots / "02_English_UI.png", figures / "04_英文界面.png"),
    ]
    for source, target in figure_sources:
        if source.exists():
            shutil.copy2(source, target)

    shutil.copy2(package / "triples_full.csv", triples_dir / "triples_full.csv")
    shutil.copy2(package / "triples_full.jsonl", triples_dir / "triples_full.jsonl")

    # stratified sample for Excel / quick inspection
    step = max(1, math.ceil(total / 200))
    sample = relations[::step][:200]
    sample_path = triples_dir / "样例_200条.csv"
    with sample_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(sample)

    # distributions
    families = Counter(row["family"] for row in relations)
    pairs = Counter((row["subject_type"], row["object_type"]) for row in relations)
    predicates = Counter(row["predicate"] for row in relations)
    polarity = Counter(row["polarity"] for row in relations)
    modality = Counter(row["modality"] for row in relations)
    review = Counter(row["review_status"] for row in relations)
    source = Counter(row["source"] for row in relations)
    per_paper = Counter(row["paper_id"] for row in relations)
    missing_line = sum(1 for row in relations if not row["evidence_line"].strip())
    direction_bad = sum(1 for row in relations if row["direction_ok"].strip().lower() == "false")
    subjects = {row["subject_id"] for row in relations}
    objects = {row["object_id"] for row in relations}
    paper_counts = sorted(per_paper.values())

    summary = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "package_version": manifest.get("version"),
        "papers": manifest.get("papers"),
        "relations": total,
        "unique_relation_ids": len({row["relation_id"] for row in relations}),
        "concepts": manifest.get("concepts"),
        "instances": manifest.get("instances"),
        "in_graph_nodes": manifest.get("in_graph_nodes"),
        "searchable_only_nodes": manifest.get("searchable_only_nodes"),
        "evidence_shards": manifest.get("evidence_shards"),
        "evidence_line_missing": missing_line,
        "evidence_line_coverage": pct(total - missing_line, total),
        "direction_flagged": direction_bad,
        "direction_flagged_share": pct(direction_bad, total),
        "distinct_subjects": len(subjects),
        "distinct_objects": len(objects),
        "relations_per_paper": {
            "min": min(paper_counts), "median": statistics.median(paper_counts),
            "max": max(paper_counts), "mean": round(total / len(paper_counts), 1),
        },
        "by_family": dict(families.most_common()),
        "by_polarity": dict(polarity.most_common()),
        "by_modality": dict(modality.most_common()),
        "by_review_status": dict(review.most_common()),
        "by_source": dict(source.most_common()),
        "input_stats": manifest.get("input_stats", {}),
    }
    (stats_dir / "概览.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1),
                                       encoding="utf-8")

    with (stats_dir / "谓词族分布.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["谓词族", "关系数", "占比"])
        for family, count in families.most_common():
            writer.writerow([family, count, pct(count, total)])

    with (stats_dir / "类型对Top30.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["主语类型", "宾语类型", "关系数"])
        for (subject_type, object_type), count in pairs.most_common(30):
            writer.writerow([subject_type, object_type, count])

    papers_meta = meta.get("papers_meta", {})
    with (stats_dir / "论文关系量.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["paper_id", "论文标题", "关系数"])
        for paper_id, count in per_paper.most_common():
            writer.writerow([paper_id, (papers_meta.get(paper_id) or {}).get("title", ""), count])

    top_papers = per_paper.most_common(8)
    top_paper_lines = "\n".join(
        f"- {paper_id[:3]} · {(papers_meta.get(paper_id) or {}).get('title', paper_id)}：{count} 条"
        for paper_id, count in top_papers)

    readme = f"""# 材料专业术语知识图谱 · 进度汇报包

生成时间：{summary['generated']}　数据版本：{manifest.get('data_version')}　包版本：{manifest.get('version')}

## 一、包内清单

| 目录 | 文件 | 内容 |
|---|---|---|
| `图/` | `01_知识图谱总览.png` | 汇报用总图（2600×1600，标题 + 统计 + 图例） |
| | `02_交互界面_全库大图.png` | 实际页面截图（12 类型区域 + 社区斑块） |
| | `03_类型汇总.png` | 12 个类型的汇总环图 |
| | `04_英文界面.png` | 中英文切换后的界面 |
| `三元组/` | `triples_full.csv` | 全量三元组，{total:,} 行，18 列，UTF-8 BOM（Excel 直接打开） |
| | `triples_full.jsonl` | 同一批三元组，{total:,} 行 JSON，字段更全 |
| | `样例_200条.csv` | 从全量中均匀抽样 200 条，用于快速浏览 |
| `统计/` | `概览.json` | 规模、覆盖、质量口径汇总 |
| | `谓词族分布.csv` | 各类关系的数量与占比 |
| | `类型对Top30.csv` | 最常见的「主语类型 → 宾语类型」组合 |
| | `论文关系量.csv` | 285 篇论文各自的关系数 |

## 二、规模与质量口径

| 指标 | 数值 |
|---|---|
| 论文 | {manifest.get('papers'):,} 篇 |
| 概念 | {manifest.get('concepts'):,} 个（12 类） |
| 论文内实例 | {manifest.get('instances'):,} 个 |
| 规范关系 | {total:,} 条（唯一 `relation_id` {summary['unique_relation_ids']:,} 个） |
| 涉及节点 | {manifest.get('in_graph_nodes'):,} 个有关系连接 + {manifest.get('searchable_only_nodes'):,} 个仅检索 |
| 证据行号覆盖 | {total - missing_line:,} / {total:,}（{summary['evidence_line_coverage']}） |
| 方向待复核 | {direction_bad} 条（{summary['direction_flagged_share']}） |
| 每篇关系数 | 最少 {summary['relations_per_paper']['min']}，中位 {summary['relations_per_paper']['median']:.0f}，最多 {summary['relations_per_paper']['max']}，平均 {summary['relations_per_paper']['mean']} |

关系最多的论文：

{top_paper_lines}

计数口径：CSV 行数 = JSONL 行数 = 唯一 `relation_id` 数。关系用 `relation_id` 去重，同一规范关系在不同论文中的出现各自保留。

## 三、图怎么用

- `01_知识图谱总览.png`：适合直接放进汇报 PPT。12 个类型区域，区域内的彩色斑块是关系聚类社区；底部是社区图例。
- `02_交互界面_全库大图.png`：展示实际产品的侧栏、筛选和统计条；页面可缩放、悬停高亮、点节点看证据。
- `03_类型汇总.png`：适合讲“知识库覆盖哪些类型、类型之间怎么连”。
- `04_英文界面.png`：展示中英文一键切换。

## 四、三元组怎么读

一行是一条规范关系，核心是 `主语 → 谓词 → 宾语`，并带出处：

| 字段 | 含义 |
|---|---|
| `relation_id` | 关系唯一 ID（计数以此为准） |
| `subject_id` / `object_id` | 概念或实例 ID |
| `subject` / `object` | 术语文本 |
| `predicate` | 规范谓词 |
| `subject_type` / `object_type` | 12 类实体类型 |
| `family` | 谓词族（effect / process / dependency / …） |
| `paper_id` | 来源论文（前 3 位是论文序号） |
| `evidence_line` / `evidence` | 原文行号与引文；行号为空表示“定位缺失” |
| `direction_ok` | 方向是否符合谓词约束；`false` 为待复核 |
| `polarity` / `modality` / `review_status` / `source` | 极性、模态、复核状态、抽取来源 |

Excel：双击 `triples_full.csv` 即可（带 BOM，中文不乱码）。
Python：

```python
import pandas as pd
df = pd.read_csv("三元组/triples_full.csv", encoding="utf-8-sig")
print(len(df), df["family"].value_counts().head())
```

```python
import json
rows = [json.loads(line) for line in open("三元组/triples_full.jsonl", encoding="utf-8")]
```

## 五、汇报要点（可直接照读）

1. 已从 {manifest.get('papers')} 篇材料论文抽出 {total:,} 条带出处的规范关系，覆盖 {manifest.get('concepts'):,} 个专业概念和 {manifest.get('instances'):,} 个论文内样品/器件实例。
2. 关系按 12 类实体和 9 类谓词族组织，可以从“材料—工艺—结构—性能—器件”链条上检索和追溯。
3. {summary['evidence_line_coverage']} 的关系能定位到原文行号和引文；其余明确标注“定位缺失”，不伪装成可核对证据。
4. 页面支持全库大图、类型汇总、术语邻域三种看法，支持按类型/谓词族/论文筛选、悬停高亮、点选看证据，以及中英文切换。
5. 质量口径是“全量守恒、端点完整、可核对、可移交”；语义准确率与召回率尚未做独立抽样评估。

## 六、已知边界

- 这是术语与关系知识库，不是问答系统或性能预测模型；观测数值只放在样品/属性信息里，不做跨论文性能排名。
- 7,135 条类型冲突、159 条方向待复核、1,475 条证据无行号仍以“复核队列”形式存在，页面会标注但不自动改写。
- 数据版本 v3.0，抽取侧的改进（摘要误删、失败块补抽、跨学科本体扩展）留待下一轮。

## 七、原始交付物

本包只放汇报用的图、三元组和统计，体积控制在 18 MB 左右，方便邮件/微信传输。
完整可交互页面（含 285 篇论文原文、证据分片，约 28 MB）不在本包内；需要演示时从项目交付目录取
`materials_kg_v3.1-delivery.zip`，解压后用本地 HTTP 服务打开：
`python -m http.server 8766 --bind 127.0.0.1 --directory materials_kg_final`，浏览器访问 `http://127.0.0.1:8766/`。
"""
    (output / "README_汇报包.md").write_text(readme, encoding="utf-8")

    files = sorted(path for path in output.rglob("*") if path.is_file())
    package_manifest = {
        "generated": summary["generated"],
        "version": manifest.get("version"),
        "papers": manifest.get("papers"),
        "relations": total,
        "concepts": manifest.get("concepts"),
        "instances": manifest.get("instances"),
        "files": {str(path.relative_to(output)).replace("\\", "/"): {
            "bytes": path.stat().st_size, "sha256": sha256(path)} for path in files},
    }
    (output / "manifest.json").write_text(json.dumps(package_manifest, ensure_ascii=False, indent=1),
                                          encoding="utf-8")

    if zip_path.exists():
        zip_path.unlink()
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(output.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(output.parent))
    return {"output": str(output), "zip": str(zip_path),
            "zip_mb": round(zip_path.stat().st_size / 1024 / 1024, 1), "files": len(files)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", default="delivery/materials_kg_final")
    parser.add_argument("--screenshots", default="delivery/验收截图")
    parser.add_argument("--output", default="delivery/材料知识图谱_汇报包_20261126")
    parser.add_argument("--zip", default="delivery/材料知识图谱_汇报包_20261126.zip")
    args = parser.parse_args()
    result = build(Path(args.package), Path(args.screenshots), Path(args.output), Path(args.zip))
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
