"""Assemble the distributable source+docs package (never includes API keys or caches)."""
from __future__ import annotations

import hashlib
import json
import platform
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "材料知识图谱_完整项目_20261126"
DIST = ROOT / "dist"
TARGET = DIST / NAME
ZIP_PATH = DIST / f"{NAME}.zip"

INCLUDE_FILES = [
    "pyproject.toml", "requirements.txt", "uv.lock", "LICENSE", ".python-version",
    "generate-graph.py", "json_to_html.py",
]
INCLUDE_DIRS = ["src", "tests", "scripts", "article", "data", "configs", "docs", "examples"]
EVAL_DIRS = ["targeted_reextract_v3", "terminology_review_20261125"]
DELIVERY_FILES = [
    "交付验收报告.md", "三元组构成分析_20261126.md",
    "materials_kg_v3.1-delivery.zip", "材料知识图谱_汇报包_20261126.zip",
]
DELIVERY_DIRS = ["验收截图"]

EXCLUDED = [
    (".kg-cache/", "LLM 回复缓存，含请求/回复文本，体积大"),
    ("evaluation/full_v1, full_v2, full_v3_*", "全量抽取/规范化数据（约 700 MB），交付 ZIP 已含最终数据"),
    ("evaluation/v2_a, v2_b, v2_in_a, v2_in_b, kg_output_eval, retry, seed10, annotate, candidates, md, tmp141, v2pilot", "中间评估数据"),
    ("delivery/materials_kg_final, delivery/materials_kg_baseline", "展开的交付包；已包含对应 ZIP"),
    ("config*.toml（根目录）", "可能含真实 API key；包内提供 configs/*.example.toml"),
    ("docs/index.html, docs/samples, docs/vendor", "上游生成的静态文档站，与本项目文档无关"),
    ("article/archive/", "上游作者样例与归档（约 40 MB），与材料流水线无关"),
    (".git, .github, .pytest_cache, __pycache__", "版本库/缓存"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ignore_pycache(directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in ("__pycache__", ".pytest_cache") or name.endswith(".pyc")}


def copy_tree(source: Path, target: Path) -> None:
    shutil.copytree(source, target, ignore=ignore_pycache)


def main() -> int:
    if not (ROOT / "README_项目说明.md").exists():
        raise SystemExit("README_项目说明.md missing")
    if TARGET.exists():
        shutil.rmtree(TARGET)
    TARGET.mkdir(parents=True)
    (TARGET / "delivery").mkdir()
    (TARGET / "evaluation").mkdir()

    shutil.copy2(ROOT / "README_项目说明.md", TARGET / "README.md")
    for name in INCLUDE_FILES:
        if (ROOT / name).exists():
            shutil.copy2(ROOT / name, TARGET / name)
    for name in INCLUDE_DIRS:
        source = ROOT / name
        if not source.exists():
            continue
        if name == "docs":
            (TARGET / "docs").mkdir()
            for doc in sorted(source.glob("*.md")):
                shutil.copy2(doc, TARGET / "docs" / doc.name)
            continue
        if name == "article":
            # scripts only: article/archive/ is 40 MB of upstream samples
            (TARGET / "article").mkdir()
            for script in sorted(source.glob("*.py")):
                shutil.copy2(script, TARGET / "article" / script.name)
            continue
        copy_tree(source, TARGET / name)

    # evaluation: scripts and small reference data only
    for path in sorted((ROOT / "evaluation").glob("*")):
        if path.is_file() and path.suffix != ".pyc":
            shutil.copy2(path, TARGET / "evaluation" / path.name)
    for name in EVAL_DIRS:
        source = ROOT / "evaluation" / name
        if source.exists():
            copy_tree(source, TARGET / "evaluation" / name)

    # delivery: reports, screenshots and the two ready-to-use zips
    for name in DELIVERY_FILES:
        source = ROOT / "delivery" / name
        if source.exists():
            shutil.copy2(source, TARGET / "delivery" / name)
    for name in DELIVERY_DIRS:
        source = ROOT / "delivery" / name
        if source.exists():
            copy_tree(source, TARGET / "delivery" / name)

    files = sorted(path for path in TARGET.rglob("*") if path.is_file())
    total_bytes = sum(path.stat().st_size for path in files)
    key_files = [TARGET / "delivery" / name for name in DELIVERY_FILES if (TARGET / "delivery" / name).exists()]
    key_files += [TARGET / "examples" / "mini_package" / "triples_full.csv"]

    manifest = [
        "# 打包清单",
        "",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- Python：{platform.python_version()}",
        f"- 文件数：{len(files)}",
        f"- 解压后大小：{total_bytes / 1024 / 1024:.1f} MB",
        f"- 源码包不含全量数据与 API key；交付 ZIP 内含 285 篇原文与全量页面数据。",
        "",
        "## 包内结构",
        "",
        "```",
        "README.md                 项目入口（本文件）",
        "docs/                     11 份代码/运行文档",
        "src/knowledge_graph/      Python 包",
        "tests/                    pytest 用例",
        "evaluation/               规范化、补抽、评估脚本 + 小体积参考数据",
        "article/                  语料处理、交付导出、汇报包脚本",
        "scripts/                  环境检查、示例、测试、打包脚本",
        "examples/                 两篇论文示例（v3 + 页面）",
        "data/samples/             上游通用图谱样例",
        "configs/                  脱敏配置示例",
        "delivery/                 验收报告、三元组分析、截图、交付 ZIP、汇报包 ZIP",
        "```",
        "",
        "## 关键文件",
        "",
        "| 文件 | 大小 | SHA-256（前 16 位） |",
        "|---|---:|---|",
    ]
    for path in key_files:
        if path.exists():
            size = path.stat().st_size
            size_text = (f"{size / 1024 / 1024:.1f} MB" if size >= 1024 * 1024
                         else f"{size / 1024:.0f} KB")
            manifest.append(f"| `{path.relative_to(TARGET).as_posix()}` | {size_text} "
                            f"| `{sha256(path)[:16]}` |")
    manifest += [
        "",
        "## 未打包内容与原因",
        "",
        "| 内容 | 原因 |",
        "|---|---|",
    ]
    for item, reason in EXCLUDED:
        manifest.append(f"| {item} | {reason} |")
    manifest += [
        "",
        "## 安全说明",
        "",
        "- 包内**没有**真实 API key；根目录的 `config*.toml` 未打包。",
        "- 使用前复制 `configs/config.materials.example.toml`，并用环境变量提供密钥：",
        "  `$env:DEEPSEEK_API_KEY = \"...\"`。",
        "- `.kg-cache/` 未打包，避免泄露请求/回复内容。",
        "",
        "## 验证",
        "",
        "```powershell",
        "python scripts/check_env.py",
        "python scripts/run_tests.ps1",
        "powershell -ExecutionPolicy Bypass -File scripts/demo_export.ps1",
        "```",
        "",
    ]
    (TARGET / "PACKAGE_MANIFEST.md").write_text("\n".join(manifest), encoding="utf-8")

    # fail closed: never ship anything that looks like a hardcoded API key
    import re
    for path in TARGET.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".py", ".md", ".toml", ".txt", ".json", ".ps1"}:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            match = re.search(r"sk-[A-Za-z0-9]{16,}", text)
            if match:
                raise SystemExit(f"refusing to package: API-key-like string in {path}: {match.group(0)[:8]}...")

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(TARGET.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(TARGET.parent))
    print(json.dumps({
        "target": str(TARGET), "zip": str(ZIP_PATH),
        "files": len(files), "uncompressed_mb": round(total_bytes / 1024 / 1024, 1),
        "zip_mb": round(ZIP_PATH.stat().st_size / 1024 / 1024, 1),
    }, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
