#!/usr/bin/env python3
"""Build the hand-off package for the 100-paper corpus.

Writes into kg_output/delivery/:
  all_triples.csv   one row per triple, with paper metadata
  summary.csv       per-paper counts
  README_交付说明.md
Then zip the site separately with: zip -r delivery/semiconductor_kg_site.zip site
"""
from __future__ import annotations

import csv
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "article" / "extracted" / "半导体论文"
KG = ARCHIVE / "kg_output"
OUT = KG / "delivery"
SUMMARY = KG / "summary.json"

FIELDS = ["paper_id", "title", "journal", "year", "subject", "predicate", "object",
          "subject_type", "object_type", "method", "via", "chunk", "source"]
COMPACT_FIELDS = ["paper_id", "subject", "predicate", "object", "subject_type", "object_type",
                  "method", "source"]
BASIC_FIELDS = ["paper_id", "subject", "predicate", "object", "subject_type", "object_type"]


def paper_meta(md_path: Path, paper_id: str) -> tuple[str, str]:
    journal = year = ""
    try:
        text = md_path.read_text(encoding="utf-8")
        m = re.search(r"\|\s*期刊\s*\|\s*([^|\n]+)", text)
        if m:
            journal = m.group(1).strip()
        m = re.search(r"\|\s*年份\s*\|\s*([^|\n]+)", text)
        if m:
            year = m.group(1).strip()
    except OSError:
        pass
    if not year:
        m = re.search(r"_(\d{4})_", paper_id)
        if m:
            year = m.group(1)
    return journal, year


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = sorted(json.load(open(SUMMARY, encoding="utf-8")), key=lambda r: r["id"])
    total = 0
    inferred = 0
    with open(OUT / "all_triples.csv", "w", encoding="utf-8-sig", newline="") as full_f, \
            open(OUT / "all_triples_compact.csv", "w", encoding="utf-8-sig", newline="") as compact_f, \
            open(OUT / "all_triples_basic.csv", "w", encoding="utf-8-sig", newline="") as basic_f:
        full_w = csv.DictWriter(full_f, fieldnames=FIELDS, extrasaction="ignore")
        compact_w = csv.DictWriter(compact_f, fieldnames=COMPACT_FIELDS, extrasaction="ignore")
        basic_w = csv.DictWriter(basic_f, fieldnames=BASIC_FIELDS, extrasaction="ignore")
        full_w.writeheader()
        compact_w.writeheader()
        basic_w.writeheader()
        for row in rows:
            paper_id = row["id"]
            journal, year = paper_meta(ARCHIVE / "semiconductor_md" / f"{paper_id}.md", paper_id)
            triples = json.load(open(KG / "enriched" / f"{paper_id}.json", encoding="utf-8"))
            for t in triples:
                record = {
                    "paper_id": paper_id,
                    "title": row.get("title", ""),
                    "journal": journal,
                    "year": year,
                    "subject": t.get("subject", ""),
                    "predicate": t.get("predicate", ""),
                    "object": t.get("object", ""),
                    "subject_type": t.get("subject_type", ""),
                    "object_type": t.get("object_type", ""),
                    "method": t.get("method", ""),
                    "via": t.get("via", ""),
                    "chunk": t.get("chunk", ""),
                    "source": t.get("source", ""),
                }
                full_w.writerow(record)
                compact_w.writerow({k: record[k] for k in COMPACT_FIELDS})
                basic_w.writerow({k: record[k] for k in BASIC_FIELDS})
                total += 1
                inferred += 1 if t.get("inferred") else 0

    shutil.copyfile(KG / "summary.csv", OUT / "summary.csv")

    readme = f"""# 半导体论文三元组抽取交付说明

## 内容

| 文件/目录 | 说明 |
|---|---|
| `site/index.html` | 100 篇论文的可浏览图谱索引（需和 `site/` 目录一起） |
| `site/papers/` | 每篇论文一个交互式图谱页面 |
| `all_triples.csv` | 全部三元组，一行一条，可直接用 Excel 打开 |
| `all_triples_compact.csv` | 精简版：三元组 + 类型 + method + source |
| `all_triples_basic.csv` | 最小版：三元组 + 类型，不含 source |
| `summary.csv` | 每篇论文的实体数、关系数、推断数、社区数 |

## 规模

- 论文：**100 篇**（同一批论文的 Markdown 与 PDF 两份，只抽一次）
- 原文抽取三元组：**{sum(int(r.get('raw_triples') or 0) for r in rows):,}** 条
- 最终三元组：**{total:,}** 条
- 其中规则推断边：**{inferred:,}** 条

## 怎么打开可视化

1. 解压后双击 `site/index.html`；
2. 如果浏览器限制本地文件，可在上级目录运行：
   `python -m http.server 8766`，然后访问 `http://127.0.0.1:8766/site/index.html`。

页面操作：

- 搜索框查找实体；
- 点击节点查看出边/入边和原文句子；
- `Communities` 按社区过滤；
- `Inferred` 开关显示/隐藏推断边（虚线）；
- `Path to another node` 查两实体间最短路径；
- `Export` 导出当前可见的 JSON/CSV/PNG。

## CSV 字段

| 字段 | 含义 |
|---|---|
| `paper_id` | 论文编号（对应 `site/papers/<paper_id>.html`） |
| `title` / `journal` / `year` | 论文标题、期刊、年份 |
| `subject` / `predicate` / `object` | 三元组 |
| `subject_type` / `object_type` | 实体类型：person, organization, place, event, technology, product, work, date, concept |
| `method` | 推断方法；`taxonomy` 表示规则推断边，空值表示原文抽取边 |
| `via` | 传递推断的中间实体（当前未启用传递推断，通常为空） |
| `chunk` | 该三元组来自第几个文本块 |
| `source` | 原文证据句（抽取边通常有，推断边为空） |

## 方法说明

- 抽取模型：DeepSeek 官方 API，`deepseek-flash`（DeepSeek-V4.1-Flash-1017）；
- 分块：800 词 / 100 词重叠；
- 文本来源：98 篇 Markdown；087、043 的 Markdown 被截断，自动改用 PDF；
- 抽取前去掉了参考文献、致谢、作者贡献等后置内容，避免大量 `published in` 类噪声；
- 实体标准化为规则版（大小写、停用词、单复数、时态合并）；未启用 LLM 实体归并；
- 推断只启用了确定性的 `taxonomy` 规则（如 `quantum computing is a computing`），因此 `method=taxonomy` 的边是规则推断，不是原文直述；
- 三元组统一小写，predicate 最多 3 个词。

## 注意

- 这是自动抽取结果，未逐条人工校验；引用具体结论时建议以 `source` 原句为准。
- 083 号论文首次抽取时单个 chunk 输出超过 16K token 被截断，已把 `max_tokens` 调到 32768 后重跑成功。
- 087、043 两篇使用 PDF 文本，PDF 抽取可能带页眉页脚，个别 `source` 句子会略碎。
"""
    (OUT / "README_交付说明.md").write_text(readme, encoding="utf-8")
    print(f"all_triples.csv / compact / basic: {total:,} rows each ({inferred:,} inferred)")
    print(f"summary.csv copied")
    print(f"delivery dir: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
