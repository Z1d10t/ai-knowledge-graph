# -*- coding: utf-8 -*-
"""Retry only the chunks that failed in a run, then rebuild via --re-enrich.

Parallel (8 workers). Merges recovered triples into raw/<paper>.json.
"""
import argparse
import copy
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\ai-knowledge-graph-main"
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "article"))

from knowledge_graph.config import load_config  # noqa: E402
from knowledge_graph.main import process_documents  # noqa: E402
from knowledge_graph.text_utils import chunk_text  # noqa: E402
from extract_corpus import strip_back_matter, strip_front_matter  # noqa: E402

MD = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\材料论文\全部_285篇\md"
lock = threading.Lock()
done = {"ok": 0, "empty": 0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="full_v2")
    ap.add_argument("--config", default=os.path.join(ROOT, "config-full.toml"))
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    run_dir = os.path.join(ROOT, "evaluation", args.run, "kg_output")
    failed = json.load(open(os.path.join(run_dir, "failed_chunks.json"), encoding="utf-8"))
    config = load_config(args.config)
    cfg = copy.deepcopy(config)
    cfg.setdefault("standardization", {})["enabled"] = False
    cfg.setdefault("inference", {})["enabled"] = False

    jobs = []
    for paper, spec in failed.items():
        md_path = os.path.join(MD, paper + ".md")
        if not os.path.exists(md_path):
            continue
        text = open(md_path, encoding="utf-8").read()
        text, _ = strip_front_matter(text)
        text, _ = strip_back_matter(text)
        chunks = chunk_text(text, cfg["chunking"]["chunk_size"], cfg["chunking"]["overlap"])
        for i in sorted(set(spec.get("empty_failed", []) + spec.get("skipped", []))):
            if 1 <= i <= len(chunks):
                jobs.append((paper, i, chunks[i - 1]))

    print(f"chunks to retry: {len(jobs)}", flush=True)

    def work(job):
        paper, idx, chunk = job
        stats = {}
        try:
            got = process_documents(cfg, [(paper + ".md", chunk)], continue_on_error=True, stats=stats)
        except Exception as e:
            return paper, idx, [], f"err:{type(e).__name__}"
        return paper, idx, got or [], ""

    buf = {}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = [ex.submit(work, j) for j in jobs]
        for fut in as_completed(futures):
            paper, idx, got, err = fut.result()
            with lock:
                if got:
                    done["ok"] += 1
                    buf.setdefault(paper, []).extend((idx, t) for t in got)
                    print(f"[{done['ok']}/{len(jobs)}] {paper[:44]} chunk {idx}: {len(got)} triples", flush=True)
                else:
                    done["empty"] += 1

    for paper, items in buf.items():
        raw_path = os.path.join(run_dir, "raw", paper + ".json")
        raw = json.load(open(raw_path, encoding="utf-8")) if os.path.exists(raw_path) else []
        for idx, t in items:
            t["chunk"] = idx
            t["paper_id"] = paper
        raw.extend(t for _, t in items)
        json.dump(raw, open(raw_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"\nrecovered {done['ok']} chunks, still empty {done['empty']}")
    print("next: extract_corpus.py --re-enrich on the same output dir")


if __name__ == "__main__":
    main()
