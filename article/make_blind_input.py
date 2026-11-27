# -*- coding: utf-8 -*-
"""Build a blind-test input: 5 papers NOT used while tuning the materials profile."""
import csv
import os
import re

ROOT = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目"
CORPUS = os.path.join(ROOT, "材料论文", "全部_285篇")
PROJ = os.path.join(ROOT, "ai-knowledge-graph-main")
OUT = os.path.join(PROJ, "article", "extracted", "semiconductor_blind", "md")
os.makedirs(OUT, exist_ok=True)

BLIND = [45, 75, 135, 195, 255]
rows = list(csv.DictReader(open(os.path.join(CORPUS, "索引_285篇.csv"), encoding="utf-8-sig")))
by_no = {int(r["统一编号"]): r for r in rows}

ABSTRACT_RE = re.compile(r"(?im)^\s*(?:#+\s*)?(?:\*\*)?\s*(abstract|summary)\b")
AFFIL_RE = re.compile(r"(?i)\b(affiliations?|corresponding author|e-?mails?)\b")
HEADER_RE = re.compile(r"(?i)^(received|accepted|published|doi|keywords|affiliations?|corresponding|"
                       r"submitted manuscript|contents?|citation|version|preprint)")


def looks_like_authors(s):
    if s.count(",") < 4:
        return False
    if s.count(",") < 8 and any(p in s[:260] for p in (". ", "! ", "? ", "; ")):
        return False
    words = [w for w in re.split(r"[\s,]+", s) if w]
    return len(words) >= 8 and sum(1 for w in words if w[:1].isupper()) / len(words) > 0.55


def clean(text):
    m = re.search(r"(?m)^---\s*$", text)
    if m and m.start() < 1500:
        text = text[m.end():].lstrip()
    m = ABSTRACT_RE.search(text, 0, 12000)
    if m:
        return text[m.start():].lstrip()
    offset = 0
    for line in text.splitlines():
        s = line.strip()
        start = offset
        offset += len(line) + 1
        if (not s or s.startswith(">") or "<sup>" in s.lower() or HEADER_RE.match(s.lstrip("*_ "))
                or AFFIL_RE.search(s) or looks_like_authors(s)):
            continue
        if s.startswith("|"):
            parts = [p.strip() for p in s.split("|") if p.strip()]
            if parts and len(parts[-1]) > 250:
                s = parts[-1]
        if len(s) < 300 or sum(ch.isdigit() for ch in s) / len(s) > 0.08:
            continue
        return text[start:].lstrip()
    return text


for n in BLIND:
    r = by_no[n]
    body = clean(open(os.path.join(CORPUS, "md", r["MD 文件"]), encoding="utf-8").read())
    open(os.path.join(OUT, r["MD 文件"]), "w", encoding="utf-8").write(body)
    print("%3d  %-24s %s  words=%d  %s" % (n, r["期刊"][:24], r["年份"], len(body.split()), body[:70].replace("\n", " ")))
