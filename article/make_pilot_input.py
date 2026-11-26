# -*- coding: utf-8 -*-
"""Build the 10-paper pilot input with proper front-matter cleaning.

Per paper:
  1. drop the metadata table our PDF->MD conversion puts on top (期刊/年份/引用量/DOI);
  2. drop cover page, running line numbers, title, author list and affiliations;
  3. keep the abstract onwards.
"""
import csv
import os
import re

ROOT = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目"
CORPUS = os.path.join(ROOT, "材料论文", "全部_285篇")
PROJ = os.path.join(ROOT, "ai-knowledge-graph-main")
PILOT = os.path.join(PROJ, "article", "extracted", "semiconductor_pilot", "md")
os.makedirs(PILOT, exist_ok=True)

PICKS = [1, 30, 60, 90, 120, 150, 180, 210, 240, 270]
rows = list(csv.DictReader(open(os.path.join(CORPUS, "索引_285篇.csv"), encoding="utf-8-sig")))
by_no = {int(r["统一编号"]): r for r in rows}

ABSTRACT_RE = re.compile(r"(?im)^\s*(?:#+\s*)?(?:\*\*)?\s*(abstract|summary)\b")
AFFIL_RE = re.compile(r"(?i)\b(affiliations?|corresponding author|e-?mails?)\b")
HEADER_RE = re.compile(r"(?i)^(received|accepted|published|doi|keywords|affiliations?|corresponding|"
                       r"submitted manuscript|contents?|citation)")


def strip_metadata_table(text):
    m = re.search(r"(?m)^---\s*$", text)
    if m and m.start() < 1500:
        return text[m.end():].lstrip()
    return text


def _looks_like_authors(s):
    """Name lists: many commas, capitalised tokens, no sentence punctuation."""
    if s.count(",") < 4:
        return False
    if s.count(",") < 8 and any(p in s[:260] for p in (". ", "! ", "? ", "; ")):
        return False
    words = [w for w in re.split(r"[\s,]+", s) if w]
    if len(words) < 8:
        return False
    caps = sum(1 for w in words if w[:1].isupper())
    return caps / len(words) > 0.55


def strip_front_matter(text):
    """Start at the abstract when there is one; otherwise at the first real body paragraph."""
    m = ABSTRACT_RE.search(text, 0, 12000)
    if m:
        return text[m.start():].lstrip()

    lines = text.splitlines()
    offset = 0
    for line in lines:
        s = line.strip()
        start = offset
        offset += len(line) + 1
        if not s or s.startswith(">"):
            continue
        plain = s.lstrip("*_ ").strip()
        if "<sup>" in s.lower() or HEADER_RE.match(plain) or AFFIL_RE.search(s):
            continue
        if _looks_like_authors(s):
            continue
        # table row: "|Check for updates|Abstract text ..." -> keep the prose part
        if s.startswith("|"):
            parts = [p.strip() for p in s.split("|") if p.strip()]
            if parts and len(parts[-1]) > 250:
                s = parts[-1]
        if len(s) < 300:
            continue
        digits = sum(ch.isdigit() for ch in s) / len(s)
        if digits > 0.08:
            continue
        return text[start:].lstrip()
    return text


report = []
for n in PICKS:
    r = by_no[n]
    src = os.path.join(CORPUS, "md", r["MD 文件"])
    body = strip_front_matter(strip_metadata_table(open(src, encoding="utf-8").read()))
    dst = os.path.join(PILOT, r["MD 文件"])
    open(dst, "w", encoding="utf-8").write(body)
    head = body[:150].replace("\n", " ")
    report.append((n, len(body.split()), head))

for n, w, head in report:
    print(f"{n:3d}  words={w:<6} {head}")
print("\nfiles:", len(os.listdir(PILOT)))
