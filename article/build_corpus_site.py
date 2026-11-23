#!/usr/bin/env python3
"""Render the 100-paper corpus as a browsable static site.

Reads the enriched triples produced by article/extract_corpus.py and writes:

  kg_output/site/index.html          searchable card index
  kg_output/site/papers/<id>.html    one interactive graph per paper
  kg_output/site/vendor/             shared vis-network library

No LLM calls: community labels are the top entity of each Louvain community.
"""
from __future__ import annotations

import html
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from knowledge_graph.visualization import build_graph_data, render_html  # noqa: E402

ARCHIVE = ROOT / "article" / "extracted" / "半导体论文"
KG = ARCHIVE / "kg_output"
SITE = KG / "site"
PAPERS = SITE / "papers"
VENDOR = SITE / "vendor"
SUMMARY = KG / "summary.json"


def paper_meta(md_path: Path, paper_id: str) -> tuple[str, str]:
    """Journal and year from the Markdown metadata table, with a filename fallback."""
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


def render_index(rows: list[dict]) -> str:
    total_raw = sum(int(r.get("raw_triples") or 0) for r in rows)
    total_enriched = sum(int(r.get("enriched_triples") or 0) for r in rows)
    total_inferred = sum(int(r.get("inferred") or 0) for r in rows)
    cards = []
    for r in rows:
        card = r["card"]
        search = " ".join([card["title"], card["journal"], card["year"]]).lower()
        cards.append(
            f'<a class="card" data-search="{html.escape(search)}" href="papers/{html.escape(r["id"])}.html">'
            f'<div class="domain">{html.escape(card["journal"] or "Semiconductor paper")}'
            f'{" · " + html.escape(card["year"]) if card["year"] else ""}</div>'
            f'<div class="name">{html.escape(card["title"] or r["id"])}</div>'
            f'<div class="meta">{card["nodes"]:,} entities · {card["edges"]:,} relationships '
            f'({card["inferred"]:,} inferred) · {card["communities"]:,} communities</div>'
            f'</a>')
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Semiconductor Knowledge Graph Corpus</title>
<style>
:root {{ --bg:#fff; --fg:#1f2328; --muted:#656d76; --panel:#f6f8fa; --border:#d0d7de; --accent:#0969da; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#0d1117; --fg:#e6edf3; --muted:#8b949e; --panel:#161b22; --border:#30363d; --accent:#388bfd; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }}
main {{ max-width:1100px; margin:0 auto; padding:40px 20px 60px; }}
h1 {{ font-size:28px; margin:0 0 6px; }}
.lead {{ color:var(--muted); margin:0 0 18px; }}
.stats {{ display:flex; gap:22px; flex-wrap:wrap; margin:0 0 22px; font-size:14px; color:var(--muted); }}
.stats b {{ color:var(--fg); font-size:16px; }}
#q {{ width:100%; max-width:460px; padding:9px 12px; border:1px solid var(--border); border-radius:8px; background:var(--bg); color:var(--fg); font:inherit; margin-bottom:20px; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:14px; }}
.card {{ display:block; text-decoration:none; color:inherit; border:1px solid var(--border); background:var(--panel); border-radius:12px; padding:16px 18px; }}
.card:hover {{ border-color:var(--accent); }}
.card .domain {{ color:var(--accent); font-size:12px; text-transform:uppercase; letter-spacing:.05em; margin-bottom:5px; }}
.card .name {{ font-weight:650; font-size:16px; line-height:1.35; }}
.card .meta {{ color:var(--muted); font-size:12.5px; margin-top:8px; }}
.note {{ color:var(--muted); font-size:13px; margin-top:24px; }}
.hidden {{ display:none; }}
code {{ background:var(--panel); border:1px solid var(--border); border-radius:4px; padding:1px 6px; font-size:13px; }}
</style>
</head>
<body>
<main>
  <h1>Semiconductor Knowledge Graph Corpus</h1>
  <p class="lead">Click a paper to explore its graph: search entities, click a node for relationships and source sentences, trace paths, filter by community or entity type.</p>
  <div class="stats">
    <span><b>{len(rows)}</b> papers</span>
    <span><b>{total_raw:,}</b> extracted triples</span>
    <span><b>{total_enriched:,}</b> final triples</span>
    <span><b>{total_inferred:,}</b> inferred</span>
  </div>
  <input id="q" type="search" placeholder="Filter by title, journal or year…" autocomplete="off">
  <div class="grid" id="grid">
    {''.join(cards)}
  </div>
  <p class="note hidden" id="empty">No papers match.</p>
  <p class="note">Solid lines are relationships extracted from the paper; dashed lines are rule-based taxonomy inference.
    References, acknowledgements and author-contribution sections were removed before extraction.</p>
</main>
<script>
const q = document.getElementById('q'), grid = document.getElementById('grid'), empty = document.getElementById('empty');
const cards = Array.from(document.querySelectorAll('.card'));
q.addEventListener('input', () => {{
  const term = q.value.trim().toLowerCase();
  let shown = 0;
  cards.forEach(c => {{
    const hit = !term || c.dataset.search.includes(term);
    c.classList.toggle('hidden', !hit);
    if (hit) shown++;
  }});
  empty.classList.toggle('hidden', shown !== 0);
}});
</script>
</body>
</html>
"""


def main() -> int:
    rows = json.load(open(SUMMARY, encoding="utf-8"))
    rows.sort(key=lambda r: r["id"])
    PAPERS.mkdir(parents=True, exist_ok=True)
    VENDOR.mkdir(parents=True, exist_ok=True)
    started_all = time.time()

    for index, row in enumerate(rows, start=1):
        paper_id = row["id"]
        enriched_path = KG / "enriched" / f"{paper_id}.json"
        md_path = ARCHIVE / "semiconductor_md" / f"{paper_id}.md"
        started = time.time()
        try:
            triples = json.load(open(enriched_path, encoding="utf-8"))
            data = build_graph_data(triples, show_inferred=True, theme="light", edge_labels="all",
                                    title_case=True, collapse_parallel_edges=True)
            for community in data["meta"]["communities"]:
                if community.get("top"):
                    community["name"] = community["top"][0]
            data["meta"]["libraryUrl"] = "../index.html"
            page = render_html(data, library_dir=str(VENDOR), page_dir=str(PAPERS))
            (PAPERS / f"{paper_id}.html").write_text(page, encoding="utf-8")

            stats = data["meta"]["stats"]
            journal, year = paper_meta(md_path, paper_id)
            row["card"] = {
                "title": row.get("title") or paper_id,
                "journal": journal,
                "year": year,
                "nodes": stats["nodes"],
                "edges": stats["edges"],
                "inferred": stats["inferred_edges"],
                "communities": stats["communities"],
            }
            print(f"[{index}/{len(rows)}] {paper_id[:55]}: {stats['nodes']} nodes, "
                  f"{stats['edges']} edges, {time.time() - started:.1f}s", flush=True)
        except Exception as e:
            print(f"[{index}/{len(rows)}] {paper_id}: ERROR {type(e).__name__}: {e}", flush=True)

    (SITE / "index.html").write_text(render_index(rows), encoding="utf-8")
    print(f"\nSite: {SITE / 'index.html'}")
    print(f"Pages: {len(list(PAPERS.glob('*.html')))}  Time: {time.time() - started_all:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
