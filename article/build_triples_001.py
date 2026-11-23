#!/usr/bin/env python3
"""Build triples for paper 001 following this project's extraction rules.

One-off manual extraction kept as a record (it was produced before the API
pipeline existed). For the DeepSeek batch pipeline use article/extract_corpus.py.

The triples below were written against `knowledge_graph.prompts.MAIN_USER_PROMPT`
(lower-case SPO, 1-3 word predicates, atomic entities, closed entity-type set,
consistent naming, no pronouns, no self-loops). The project's own helpers are then
used to enforce the predicate limit and to attach `chunk` / `source` provenance,
so the output matches what `generate-graph` writes (single document: no `document`).

Usage: python article/build_triples_001.py
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from knowledge_graph.config import load_config  # noqa: E402
from knowledge_graph.entity_standardization import limit_predicate_length  # noqa: E402
from knowledge_graph.text_utils import chunk_text, split_sentences  # noqa: E402
from knowledge_graph.visualization import ENTITY_TYPES  # noqa: E402

PAPER = os.path.join(
    ROOT, "article", "extracted", "半导体论文", "semiconductor_md",
    "001_Chen_2024_Improved-charge-extraction-in-inverted-perovskit.md",
)
OUT = os.path.join(
    ROOT, "article", "extracted", "半导体论文", "triples_001_Chen_2024.json",
)

WORK = "work"
TITLE = "improved charge extraction in inverted perovskite solar cells with dual-site-binding ligands"

# (subject, predicate, object, subject_type, object_type)
TRIPLES = [
    # ---- article metadata ------------------------------------------------- #
    (TITLE, "published in", "science", WORK, WORK),
    (TITLE, "published in", "2024", WORK, "date"),
    ("hao chen", "authored", TITLE, "person", WORK),
    ("cheng liu", "authored", TITLE, "person", WORK),
    ("jian xu", "authored", TITLE, "person", WORK),
    ("bin chen", "supervised", TITLE, "person", WORK),
    ("zhijun ning", "supervised", TITLE, "person", WORK),
    ("edward h. sargent", "supervised", TITLE, "person", WORK),
    ("hao chen", "affiliated with", "northwestern university", "person", "organization"),
    ("hao chen", "affiliated with", "university of toronto", "person", "organization"),
    ("zhijun ning", "affiliated with", "shanghaitech university", "person", "organization"),

    # ---- abstract --------------------------------------------------------- #
    ("inverted perovskite solar cells", "improve", "operating stability", "technology", "concept"),
    ("inverted perovskite solar cells", "lag behind", "nip perovskite solar cells", "technology", "technology"),
    ("power conversion efficiency deficit", "occurs at", "charge-transport layer interface", "concept", "concept"),
    ("charge-transport layer interface", "limits", "power conversion efficiency", "concept", "concept"),
    ("passivating ligands", "bind to", "single active binding site", "technology", "concept"),
    ("dense ligand packing", "forms", "resistive barrier", "concept", "concept"),
    ("resistive barrier", "limits", "fill factor", "concept", "concept"),
    ("dual-site-binding ligands", "bind to", "neighboring pb2+ defects", "technology", "concept"),
    ("dual-site-binding ligands", "adopt", "planar orientation", "technology", "concept"),
    ("inverted perovskite solar cells", "achieve", "26.15% pce", "technology", "concept"),
    ("inverted perovskite solar cells", "achieve", "24.74% pce", "technology", "concept"),
    ("inverted perovskite solar cells", "retain", "95% initial pce", "technology", "concept"),
    ("inverted perovskite solar cells", "operated for", "1200 hours", "technology", "concept"),
    ("ligand orientation", "affects", "charge extraction", "concept", "concept"),
    ("dual-site-binding ligands", "increase", "qss pce", "technology", "concept"),

    # ---- introduction ----------------------------------------------------- #
    ("perovskite solar cells", "reach", "25.7% pce", "technology", "concept"),
    ("nip perovskite solar cells", "achieve", "highest certified pce", "technology", "concept"),
    ("nip perovskite solar cells", "lack", "operating stability", "technology", "concept"),
    ("inverted perovskite solar cells", "avoid", "p-type dopants", "technology", "concept"),
    ("inverted perovskite solar cells", "reach", "25.1% pce", "technology", "concept"),
    ("band misalignment", "limits", "power conversion efficiency", "concept", "concept"),
    ("energy-level pinning", "limits", "power conversion efficiency", "concept", "concept"),
    ("surface defects", "aggravate", "energetic losses", "concept", "concept"),
    ("undercoordinated pb2+", "causes", "nonradiative recombination", "concept", "concept"),
    ("nonradiative recombination", "limits", "photovoltage", "concept", "concept"),
    ("nonradiative recombination", "limits", "fill factor", "concept", "concept"),
    ("surface passivation", "suppresses", "nonradiative recombination", "concept", "concept"),
    ("ammonium ligands", "passivate", "perovskite surface", "technology", "concept"),
    ("bulk additives", "passivate", "perovskite", "technology", "technology"),
    ("perpendicular ligand alignment", "creates", "resistive barrier", "concept", "concept"),
    ("resistive barrier", "blocks", "charge transport", "concept", "concept"),

    # ---- theoretical investigations -------------------------------------- #
    ("benzene ring", "has", "flat structure", "concept", "concept"),
    ("flat structure", "lies parallel to", "perovskite surface", "concept", "concept"),
    ("sulfonate group", "coordinates with", "pb2+", "concept", "concept"),
    ("phosphonate group", "coordinates with", "pb2+", "concept", "concept"),
    ("oxygen atoms", "correlate with", "strong binding", "concept", "concept"),
    ("ligand length", "determines", "multi-site binding", "concept", "concept"),
    ("pb sites", "are spaced", "6.3 å", "concept", "concept"),
    ("benzenesulfonate", "is a", "sulfonate ligand", "technology", "technology"),
    ("bzs", "has", "5.7 å length", "technology", "concept"),
    ("density functional theory", "investigates", "ligand orientation", "technology", "concept"),
    ("4cl-bzs", "contains", "chloride group", "technology", "concept"),
    ("4ch3-bzs", "contains", "methyl group", "technology", "concept"),
    ("4cl-bzs", "has", "6.37 å length", "technology", "concept"),
    ("4ch3-bzs", "has", "6.14 å length", "technology", "concept"),
    ("4cl-bzs", "prefers", "parallel orientation", "technology", "concept"),
    ("bzs", "prefers", "perpendicular orientation", "technology", "concept"),
    ("4ch3-bzs", "prefers", "perpendicular orientation", "technology", "concept"),
    ("chloride group", "binds to", "pb2+", "concept", "concept"),
    ("4cl-bzs", "enables", "dual-site passivation", "technology", "concept"),
    ("c60", "is used as", "electron transport layer", "technology", "technology"),
    ("c60", "induces", "energetic losses", "technology", "concept"),
    ("4cl-bzs", "binds strongly to", "c60", "technology", "technology"),
    ("4cl-bzs", "strengthens", "perovskite/c60 interface", "technology", "concept"),
    ("bzs", "binds weakly to", "c60", "technology", "technology"),
    ("4ch3-bzs", "binds weakly to", "c60", "technology", "technology"),

    # ---- ligand-perovskite binding --------------------------------------- #
    ("bzs", "diffuses to", "top surface", "technology", "concept"),
    ("4ch3-bzs", "diffuses to", "top surface", "technology", "concept"),
    ("4cl-bzs", "diffuses to", "top surface", "technology", "concept"),
    ("passivating ligands", "do not enter", "perovskite lattice", "technology", "concept"),
    ("tof-sims", "shows", "ligand distribution", "technology", "concept"),
    ("x-ray diffraction", "shows", "no lattice change", "technology", "concept"),
    ("scanning electron microscopy", "shows", "uniform morphology", "technology", "concept"),
    ("x-ray photoelectron spectroscopy", "shows", "pb 4f peak shift", "technology", "concept"),
    ("x-ray photoelectron spectroscopy", "shows", "cl-pb interaction", "technology", "concept"),
    ("nuclear magnetic resonance", "shows", "cl-pb interaction", "technology", "concept"),

    # ---- optoelectronic characterization --------------------------------- #
    ("4cl-bzs", "increases", "photoluminescence quantum yield", "technology", "concept"),
    ("photoluminescence quantum yield increase", "corresponds to", "qfls increase", "concept", "concept"),
    ("4cl-bzs", "increases", "qfls", "technology", "concept"),
    ("4cl-bzs", "reduces", "interface losses", "technology", "concept"),
    ("4cl-bzs", "increases", "carrier lifetime", "technology", "concept"),
    ("time-resolved photoluminescence", "measures", "carrier lifetime", "technology", "concept"),
    ("4cl-bzs/c60 stack", "shows", "efficient electron transfer", "concept", "concept"),
    ("4cl-bzs", "reduces", "trap density", "technology", "concept"),
    ("4cl-bzs", "accelerates", "photocurrent decay", "technology", "concept"),
    ("4cl-bzs", "improves", "electron extraction", "technology", "concept"),
    ("ultraviolet photoelectron spectroscopy", "shows", "reduced conduction band offset", "technology", "concept"),
    ("bzs", "increases", "conduction band offset", "technology", "concept"),
    ("4ch3-bzs", "increases", "conduction band offset", "technology", "concept"),
    ("kelvin probe force microscopy", "confirms", "ups trend", "technology", "concept"),
    ("density functional theory", "confirms", "ups trend", "technology", "concept"),

    # ---- inverted perovskite solar cells --------------------------------- #
    ("inverted perovskite solar cells", "use", "4cl-bzs", "technology", "technology"),
    ("inverted perovskite solar cells", "have structure",
     "fto/sam/perovskite/c60/snox/ag", "technology", "technology"),
    ("perovskite layer", "has thickness", "900 nm", "technology", "concept"),
    ("control devices", "achieve", "24% pce", "technology", "concept"),
    ("4cl-bzs treated devices", "achieve", "26.3% pce", "technology", "concept"),
    ("4cl-bzs", "increases", "open-circuit voltage", "technology", "concept"),
    ("4cl-bzs", "increases", "fill factor", "technology", "concept"),
    ("fill factor improvement", "results from", "enhanced charge extraction", "concept", "concept"),
    ("donating group", "enables", "dual-site passivation", "concept", "concept"),
    ("4f-bzsa", "achieves", "comparable pce", "technology", "concept"),
    ("4i-bzsa", "improves", "power conversion efficiency", "technology", "concept"),
    ("bimolecular surface passivation", "combines", "chemical passivation", "technology", "concept"),
    ("bimolecular surface passivation", "combines", "field-effect passivation", "technology", "concept"),
    ("bimolecular surface passivation", "increases", "photoluminescence quantum yield", "technology", "concept"),
    ("combined treatment", "achieves", "26.9% pce", "concept", "concept"),
    ("combined treatment", "achieves", "1.18 v", "concept", "concept"),
    ("combined treatment", "achieves", "86.2% fill factor", "concept", "concept"),
    ("combined treatment", "achieves", "26.4 ma/cm2", "concept", "concept"),
    ("inverted perovskite solar cells", "has", "1.53 ev bandgap", "technology", "concept"),
    ("external quantum efficiency", "measures", "bandgap", "technology", "concept"),
    ("newport", "certifies", "26.15% pce", "organization", "concept"),
    ("newport", "certifies", "24.74% pce", "organization", "concept"),
    ("inverted perovskite solar cells", "surpass", "nip perovskite solar cells", "technology", "technology"),
    ("isos-d-2i", "tests", "thermal stability", "concept", "concept"),
    ("4cl-bzs treated devices", "retain", "95% pce after 1500 hours", "technology", "concept"),
    ("isos-l-3", "tests", "operating stability", "concept", "concept"),
    ("4cl-bzs treated devices", "achieve", "t95 1200 hours", "technology", "concept"),
    ("control devices", "drop from", "22% pce", "technology", "concept"),
    ("4cl-bzs treated devices", "achieve", "t87 540 hours", "technology", "concept"),

    # ---- discussion ------------------------------------------------------- #
    ("4cl-bzs", "passivates", "undercoordinated pb2+", "technology", "concept"),
    ("4cl-bzs", "reduces", "surface defect density", "technology", "concept"),
    ("4cl-bzs", "minimizes", "energetic mismatch", "technology", "concept"),
    ("energetic mismatch", "exists at", "perovskite/c60 interface", "concept", "concept"),
    ("planar ligand orientation", "improves", "pin psc performance", "concept", "concept"),
    ("4cl-bzs", "works for", "wide-bandgap perovskites", "technology", "technology"),
    ("4cl-bzs", "works for", "narrow-bandgap perovskites", "technology", "technology"),
    ("wide-bandgap perovskites", "used in", "tandem solar cells", "technology", "technology"),
    ("narrow-bandgap perovskites", "used in", "tandem solar cells", "technology", "technology"),
    ("4cl-bzs", "increases", "power conversion efficiency", "technology", "concept"),
]

_TOKEN = re.compile(r"[a-z0-9][a-z0-9.%/+-]*")
_NUM = re.compile(r"^\d+(?:\.\d+)?%?$")
_ALIASES = {
    "power conversion efficiency": ("pce",),
    "photoluminescence quantum yield": ("plqy",),
    "quasi-fermi level splitting": ("qfls",),
    "open-circuit voltage": ("voc",),
    "fill factor": ("ff",),
    "short-circuit current density": ("jsc",),
    "external quantum efficiency": ("eqe",),
    "density functional theory": ("dft",),
    "x-ray photoelectron spectroscopy": ("xps",),
    "ultraviolet photoelectron spectroscopy": ("ups",),
    "time-resolved photoluminescence": ("trpl",),
    "kelvin probe force microscopy": ("kpfm",),
    "x-ray diffraction": ("xrd",),
    "scanning electron microscopy": ("sem",),
    "nuclear magnetic resonance": ("nmr",),
    "time-of-flight secondary ion mass spectrometry": ("tof-sims",),
    "maximum power point": ("mpp",),
}
_STOP = {
    "the", "and", "for", "with", "from", "that", "this", "these", "those", "are", "was", "were",
    "has", "have", "had", "its", "their", "not", "but", "can", "may", "more", "than", "into", "via",
    "using", "used", "between", "after", "before", "under", "over", "based", "than", "then", "also",
}


def _tokens(name: str) -> list[str]:
    """Content tokens of an entity name: words of 3+ chars (minus stopwords) and digit tokens."""
    return [t.strip(".-") for t in _TOKEN.findall(name.lower())
            if (len(t) >= 3 and t not in _STOP) or any(ch.isdigit() for ch in t)]


def _alias_present(text: str, alias: str) -> bool:
    """Whole-word alias match (so 'ff' does not match 'favorable', 'sem' not 'semiconductor')."""
    return re.search(rf"(?<![a-z0-9]){re.escape(alias)}s?(?![a-z0-9])", text) is not None


def _score(chunk: str, name: str) -> float:
    """How well a chunk covers an entity name: token coverage, exact-phrase and numeric bonuses."""
    low = chunk.lower()
    tokens = _tokens(name)
    if any(_alias_present(low, alias) for alias in _ALIASES.get(name.lower(), ())):
        coverage = 1.0  # the paper's abbreviation is evidence for the full term
    else:
        coverage = sum(1 for t in tokens if t in low) / len(tokens) if tokens else 0.0
    numeric = [t for t in tokens if _NUM.match(t)]
    if numeric and all(t in low for t in numeric):
        coverage += 1.0  # a stated value identifies the evidence sentence better than a common word
    return coverage + (0.5 if name.lower() in low else 0.0)


def _sentence_score(sentence: str, subject: str, obj: str) -> float:
    """How well one sentence evidences the triple (presence of the object is weighted higher)."""
    return 2 * _score(sentence, obj) + _score(sentence, subject)


def _best_source(chunk: str, subject: str, obj: str, max_length: int = 300) -> str | None:
    """The sentence of the chunk that best evidences the triple."""
    sentences = split_sentences(chunk)
    if not sentences:
        return None
    best = max(sentences, key=lambda s: _sentence_score(s, subject, obj))
    if _sentence_score(best, subject, obj) < 0.5:
        return None
    best = best.strip()
    return best if len(best) <= max_length else best[:max_length - 1].rstrip() + "…"


def main() -> int:
    config = load_config(os.path.join(ROOT, "config.toml"))
    if not config:
        return 1
    chunk_size = config["chunking"]["chunk_size"]
    overlap = config["chunking"]["overlap"]

    with open(PAPER, encoding="utf-8") as f:
        text = f.read()
    chunks = chunk_text(text, chunk_size, overlap)

    seen = set()
    result, with_source = [], 0
    for subject, predicate, obj, subject_type, object_type in TRIPLES:
        subject, predicate, obj = subject.strip().lower(), predicate.strip().lower(), obj.strip().lower()
        if subject == obj:
            raise SystemExit(f"self-loop: {subject!r}")
        if (subject, predicate, obj) in seen:
            raise SystemExit(f"duplicate: {(subject, predicate, obj)!r}")
        seen.add((subject, predicate, obj))
        if subject_type not in ENTITY_TYPES or object_type not in ENTITY_TYPES:
            raise SystemExit(f"bad entity type: {subject_type!r}/{object_type!r}")

        predicate = limit_predicate_length(predicate)
        best_index = max(range(len(chunks)),
                         key=lambda i: max((_sentence_score(s, subject, obj)
                                            for s in split_sentences(chunks[i])), default=0.0))
        chunk = chunks[best_index]
        item = {"subject": subject, "predicate": predicate, "object": obj,
                "subject_type": subject_type, "object_type": object_type, "chunk": best_index + 1}
        source = _best_source(chunk, subject, obj)
        if source:
            item["source"] = source
            with_source += 1
        result.append(item)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    methods = {}
    for item in result:
        methods[item["predicate"]] = methods.get(item["predicate"], 0) + 1
    print(f"paper:   {os.path.basename(PAPER)}")
    print(f"chunks:  {len(chunks)} (chunk_size={chunk_size}, overlap={overlap})")
    print(f"triples: {len(result)}  ({with_source} with source, "
          f"{100 * with_source / len(result):.0f}%)")
    print(f"nodes:   {len({t['subject'] for t in result} | {t['object'] for t in result})}")
    print(f"output:  {os.path.relpath(OUT, ROOT)}")
    print("top predicates: " + ", ".join(
        f"{p} ({n})" for p, n in sorted(methods.items(), key=lambda kv: -kv[1])[:8]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
