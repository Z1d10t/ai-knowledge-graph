"""Check that the checkout can run the pipeline, tests and the delivery page."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

REQUIRED = ["jinja2", "networkx", "requests"]
OPTIONAL = {"fastapi": "graph-serve", "uvicorn": "graph-serve", "pypdf": "PDF input", "docx": "DOCX input"}


def main() -> int:
    print(f"python: {sys.version.split()[0]}  ({sys.executable})")
    print(f"root:   {ROOT}")
    if sys.version_info < (3, 11):
        print("FAIL: Python 3.11+ is required")
        return 1
    missing = []
    for name in REQUIRED:
        try:
            module = importlib.import_module(name)
            print(f"OK   {name} {getattr(module, '__version__', '')}")
        except Exception as error:  # noqa: BLE001
            print(f"FAIL {name}: {error}")
            missing.append(name)
    for name, purpose in OPTIONAL.items():
        try:
            importlib.import_module(name)
            print(f"OK   {name} (optional, {purpose})")
        except Exception:  # noqa: BLE001
            print(f"--   {name} (optional, {purpose}) not installed")
    try:
        import knowledge_graph
        print(f"OK   knowledge_graph package: {Path(knowledge_graph.__file__).parent}")
    except Exception as error:  # noqa: BLE001
        print(f"FAIL knowledge_graph import: {error}")
        missing.append("knowledge_graph")
    templates = ROOT / "src" / "knowledge_graph" / "templates"
    for name in ("materials_overview.html", "materials_overview.js", "materials_overview.css",
                 "graph.html.j2"):
        print(("OK   " if (templates / name).exists() else "FAIL ") + f"template {name}")
    delivery = ROOT / "delivery" / "materials_kg_final" / "index.html"
    print(("OK   " if delivery.exists() else "--   ") + "delivery package (optional)")
    if missing:
        print("\nmissing required pieces: " + ", ".join(missing))
        return 1
    print("\nenvironment looks good; try: python -m pytest tests -q")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
