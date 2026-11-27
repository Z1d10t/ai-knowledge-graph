# -*- coding: utf-8 -*-
"""Recover per-paper failed chunk indices from the full-run console log."""
import json
import os
import re

LOG = r"C:\Users\admin\AppData\Local\Temp\dsh-spill-UkvKeb\session-a96e512d8196\b48b29a5496a-job_output.txt"
OUT = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\ai-knowledge-graph-main\evaluation\full_v1\kg_output"

paper_re = re.compile(r"^\[(\d+)/285\] ([^:]+):")
fail_re = re.compile(r"Failed to extract triples from chunk (\d+)")
skip_re = re.compile(r"skipping chunk (\d+)")

current = None
data = {}
for line in open(LOG, encoding="utf-8", errors="replace"):
    m = paper_re.match(line.strip())
    if m:
        current = m.group(2).strip()
        data.setdefault(current, {"empty_failed": [], "skipped": []})
        continue
    if current is None:
        continue
    m = fail_re.search(line)
    if m:
        data[current]["empty_failed"].append(int(m.group(1)))
        continue
    m = skip_re.search(line)
    if m:
        data[current]["skipped"].append(int(m.group(1)))

summary = {k: {"empty_failed": sorted(set(v["empty_failed"])), "skipped": sorted(set(v["skipped"]))}
           for k, v in data.items()}
summary = {k: v for k, v in summary.items() if v["empty_failed"] or v["skipped"]}

path = os.path.join(OUT, "failed_chunks.json")
json.dump(summary, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

papers = len(summary)
chunks = sum(len(v["empty_failed"]) + len(v["skipped"]) for v in summary.values())
print("papers with failed chunks:", papers)
print("failed chunk count:", chunks)
for k, v in list(summary.items())[:8]:
    print(f"  {k[:48]:48} empty={len(v['empty_failed'])} skipped={len(v['skipped'])}")
print("written", path)
