# -*- coding: utf-8 -*-
"""Freeze the full-run manifest: model, prompts, config and corpus, before extraction."""
import hashlib
import json
import os
import time

ROOT = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\ai-knowledge-graph-main"
CORPUS = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\材料论文\全部_285篇"
OUT = os.path.join(ROOT, "evaluation", "full_v1")
os.makedirs(OUT, exist_ok=True)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


files = {
    "config-full.toml": os.path.join(ROOT, "config-full.toml"),
    "prompts/main_prompts.py": os.path.join(ROOT, "src", "knowledge_graph", "prompts", "main_prompts.py"),
    "prompts/__init__.py": os.path.join(ROOT, "src", "knowledge_graph", "prompts", "__init__.py"),
    "profiles.py": os.path.join(ROOT, "src", "knowledge_graph", "profiles.py"),
    "quantities.py": os.path.join(ROOT, "src", "knowledge_graph", "postprocess", "quantities.py"),
    "main.py": os.path.join(ROOT, "src", "knowledge_graph", "main.py"),
    "extract_corpus.py": os.path.join(ROOT, "article", "extract_corpus.py"),
}

import tomllib  # noqa: E402

config = tomllib.load(open(files["config-full.toml"], "rb"))
mds = sorted(f for f in os.listdir(os.path.join(CORPUS, "md")) if f.endswith(".md"))

manifest = {
    "run_id": "full_v1",
    "created": time.strftime("%Y-%m-%d %H:%M:%S"),
    "purpose": "285 篇全量 raw 抽取（v1）；结果用于后续解析重建与评估，不作为最终质量验收",
    "model": config["llm"]["model"],
    "endpoint": config["llm"]["base_url"],
    "profile": config["profile"]["name"],
    "profile_version": config["profile"]["version"],
    "llm": {k: v for k, v in config["llm"].items() if k != "api_key"},
    "chunking": config["chunking"],
    "inference": config["inference"],
    "standardization": config["standardization"],
    "code_hashes": {name: sha(path) for name, path in files.items()},
    "corpus": {"root": CORPUS, "papers": len(mds), "first": mds[0], "last": mds[-1], "files": mds},
    "outputs": {
        "raw": os.path.join(OUT, "kg_output", "raw"),
        "enriched": os.path.join(OUT, "kg_output", "enriched"),
        "failures": os.path.join(OUT, "kg_output", "failures"),
        "summary": os.path.join(OUT, "kg_output", "summary.csv"),
    },
}

path = os.path.join(OUT, "manifest.json")
json.dump(manifest, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("written", path)
print("papers:", manifest["corpus"]["papers"], "| model:", manifest["model"])
for k, v in manifest["code_hashes"].items():
    print(f"  {k:28} {v}")
