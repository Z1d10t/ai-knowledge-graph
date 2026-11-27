"""Terminology layer: professional concepts, aliases, mentions and evidence-bearing relations.

The generic pipeline treats every string a model emits as an entity. For a scientific
knowledge graph that is not enough: ``absorption coefficient enhanced by up to a factor of
two after annealing`` is a property *mention* with a number and a condition attached, not
a concept; ``organic polymers modified MOS`` is a composite mention, not a synonym of
``organic polymers``; ``FE`` in one paper is an abbreviation that must never be promoted to
a global alias of ``ferroelectric order``.

This module is the deterministic engine behind that separation. It provides:

* key functions (:func:`normalize_key`, :func:`formula_identity`) that normalise *for
  lookup only* -- chemical case, stoichiometry and phase markers are never destroyed;
* abbreviation mining from parenthetical definitions (paper-scoped by design);
* attribute-phrase splitting (concept + change + condition) and composite-mention
  detection, so long labels are never cut blindly;
* a closed concept-type vocabulary with ordered classification rules and conflict
  reporting instead of "most frequent type wins";
* a predicate-family map plus a causal-direction check that flags a property being written
  as the *cause* of a process (the 250-paper ``absorption coefficient -> improves ->
  cation disorder`` error);
* :class:`ConceptRegistry`, which assigns stable concept ids and merges labels only when
  the merge is provably safe (same formula, same plain name) -- never by substring,
  never by shared lower-case abbreviation.

Nothing here calls an LLM. The rules are intended to be reviewed and extended; every
decision carries the rule that produced it so a reviewer can audit it.
"""
from __future__ import annotations

import hashlib
import html
import re
from collections import Counter
from dataclasses import dataclass, field

# --------------------------------------------------------------------------- #
# Concept types
# --------------------------------------------------------------------------- #
#: Concept-layer types. ``sample`` is deliberately *not* here: a sample is a paper-scoped
#: experiment instance, not a professional concept (see :data:`INSTANCE_TYPES`).
CONCEPT_TYPES: tuple[str, ...] = (
    "material",          # a substance: AgBiS2, HfO2, formamidinium lead triiodide
    "material_class",    # a family: MXenes, transition metal dichalcogenides, oxides
    "component",         # functional layer / part: electron transport layer, front absorber
    "structure",         # structure / order / phase: quantum-well structure, cation disorder
    "defect",            # defect / vacancy / undercoordinated site
    "process",           # synthesis or treatment step: atomic layer deposition, exfoliation
    "characterization",  # characterization or calculation method: DFT, XRD
    "mechanism",         # mechanism / process phenomenon: nonradiative recombination
    "property",          # property / physical quantity: fill factor, breakdown voltage
    "device",            # device: solar cell, photodetector, APD
    "interface",         # interface between layers
)

#: Instance-layer types. These stay inside one paper and are never global hubs.
INSTANCE_TYPES: tuple[str, ...] = ("sample", "condition", "measurement")

#: Mapping from the types the extraction profile emits to concept-layer types. A v2
#: ``measurement`` node is a numeric observation, so it is not a concept at all.
V2_TYPE_MAP: dict[str, str | None] = {
    "material": "material",
    "material_class": "material_class",
    "defect": "defect",
    "device": "device",
    "structure": "structure",
    "process": "process",
    "characterization": "characterization",
    "mechanism": "mechanism",
    "property": "property",
    "interface": "interface",
    "component": "component",
    "sample": None,
    "condition": None,
    "measurement": None,
}

#: Type-equivalence used when deciding whether two observed types can describe one
#: concept. ``characterization`` and a measurement method both belong to "method".
TYPE_FAMILIES: dict[str, str] = {
    "material": "substance",
    "material_class": "substance",
    "component": "part",
    "structure": "form",
    "defect": "form",
    "process": "method",
    "characterization": "method",
    "mechanism": "process",
    "property": "quantity",
    "device": "object",
    "interface": "part",
}

#: Some predicates are only meaningful between certain type families. Used to flag, not
#: to silently drop: the review may still accept a flagged edge.
_CAUSAL_FAMILIES = frozenset({"method", "process"})
_QUANTITY_FAMILY = "quantity"

# Element symbols, used to recognise chemical formulas without treating Pb2+ as one.
_ELEMENTS = frozenset(
    """H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn
    Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr
    Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra
    Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr""".split()
)

#: Organic-cation abbreviations used inside perovskite formulas. Without these,
#: ``FAPbI3`` / ``MAPbI3`` would fail formula parsing and lose the phase distinction the
#: review requires (``alpha-FAPbI3`` and ``delta-FAPbI3`` must stay apart).
_PSEUDO_CATIONS = ("FA", "MA", "PEA", "BA", "OA", "EDA", "TBA", "DMA", "GA")

#: Phase / polymorph markers that must survive normalisation ("alpha-FAPbI3" stays apart
#: from "delta-FAPbI3").
_PHASE_PREFIXES = {
    "α": "alpha-", "β": "beta-", "γ": "gamma-", "δ": "delta-", "ε": "epsilon-",
    "α-": "alpha-", "β-": "beta-", "γ-": "gamma-", "δ-": "delta-", "ε-": "epsilon-",
}

_UNICODE_MAP = {
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "ε": "epsilon", "θ": "theta",
    "λ": "lambda", "μ": "u", "Å": "A", "Å": "A", "−": "-", "–": "-", "—": "-",
    "×": "x", "⋅": ".", "·": ".", "′": "'", "″": '"',
    "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5", "₆": "6", "₇": "7",
    "₈": "8", "₉": "9", "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5",
    "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9", "⁻": "-", "⁺": "+",
}

_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_DASHES_RE = re.compile(r"\s*-\s*")


def _clean(text: str) -> str:
    """Unescape entities, drop markup, fold unicode variants and normalise whitespace."""
    value = html.unescape(str(text or ""))
    value = _TAG_RE.sub(" ", value)
    for src, dst in _UNICODE_MAP.items():
        value = value.replace(src, dst)
    return _SPACE_RE.sub(" ", value).strip()


def clean_text(text: str) -> str:
    """Public form of :func:`_clean`: markup-free, unicode-folded display text."""
    return _clean(text)


def normalize_key(text: str) -> str:
    """Comparison key for label lookup (lower-case alphanumerics only).

    This key is for *finding candidates* -- it is never a merge key. ``α-FAPbI3`` and
    ``δ-FAPbI3`` deliberately collapse to different keys because the phase marker is
    normalised to a word rather than deleted.
    """
    value = _clean(text).lower()
    for src, dst in _PHASE_PREFIXES.items():
        if value.startswith(src):
            value = dst + value[len(src):]
            break
    value = value.replace("alpha-", "alpha-")
    return _NON_ALNUM_RE.sub("", value)


def formula_identity(text: str) -> str | None:
    """Case-insensitive chemical identity (stoichiometry and phase preserved) or None.

    ``HfO₂`` and ``HfO2`` share an identity; ``Sb2O3`` and ``Sb4O6`` do not; ``alpha-FAPbI3``
    and ``delta-FAPbI3`` do not.
    """
    value = _clean(text)
    phase = ""
    lowered = value.lower()
    for marker, word in (_PHASE_PREFIXES.items()):
        if lowered.startswith(marker):
            phase = word
            value = value[len(marker):]
            break
    else:
        match = re.match(r"(?i)^(alpha|beta|gamma|delta|epsilon)\s*-?\s*", value)
        if match:
            phase = match.group(1).lower() + "-"
            value = value[match.end():]
    compact = re.sub(r"\s+", "", value)
    compact = _DASHES_RE.sub("-", compact)
    if not compact:
        return None
    if not _parse_formula(compact):
        return None
    return (phase + compact).lower()


def _parse_formula(token: str) -> bool:
    """True when ``token`` parses as element symbols with optional stoichiometry.

    All-single-letter, digit-free strings of at most three symbols (``FF``, ``MOS``) are
    rejected: they are far more often acronyms than formulas.
    """
    text = re.sub(r"(?:-|,|/|\|)", "", token)
    text = re.sub(r"T[xz]?$", "", text)  # MXene surface terminations: Mo2TiC2Tx
    if not text:
        return False
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", text):
        return False
    i, elements, two_letter, has_digit = 0, 0, 0, False
    while i < len(text):
        if not text[i].isupper():
            return False
        pseudo = next((c for c in _PSEUDO_CATIONS if text.startswith(c, i)), None)
        if pseudo:
            symbol = pseudo
            i += len(pseudo)
        else:
            symbol = text[i]
            i += 1
            if i < len(text) and text[i].islower():
                symbol += text[i]
                i += 1
            if symbol not in _ELEMENTS:
                return False
            if len(symbol) > 1:
                two_letter += 1
        elements += 1
        while i < len(text) and (text[i].isdigit() or text[i] == "."):
            has_digit = True
            i += 1
    if elements <= 3 and two_letter == 0 and not has_digit:
        return False
    return elements >= 1


def looks_like_formula(text: str) -> bool:
    """Convenience wrapper: does this label read as a chemical formula?"""
    return formula_identity(text) is not None


def compact_key(text: str) -> str:
    """Lower-case alphanumeric key used to merge plain (non-abbreviation) names."""
    return _NON_ALNUM_RE.sub("", _clean(text).lower())


_SINGULAR_EXCEPTIONS = frozenset(
    {"bias", "canvas", "gas", "lens", "series", "species", "means", "physics", "analysis",
     "basis", "crisis", "thesis", "status", "apparatus", "corpus", "news", "chaos", "atlas"})


def singular_key(key: str) -> str:
    """Strip English plural marking from the last word of a compact key.

    Used only for *concept identity* so "quasi-2D perovskites" and "quasi-2D perovskite" are
    one concept. Chemical formulas are compared through :func:`formula_identity` instead, so
    a digit inside the key ("quasi2d", "hfo2") does not block plural folding; a key that ends
    in a digit is returned unchanged.
    """
    if not key or key[-1].isdigit():
        return key
    if key.endswith(("ss", "us", "is", "as", "os", "ys")) or key in _SINGULAR_EXCEPTIONS:
        return key
    if key.endswith("ies") and len(key) > 4:
        return key[:-3] + "y"
    if key.endswith(("ses", "xes", "ches", "shes", "zes")):
        return key[:-2]
    if key.endswith("s") and len(key) > 2:
        return key[:-1]
    return key


def is_abbreviation(text: str) -> bool:
    """True for short all-caps style labels such as ``TMDCs``, ``APDs``, ``STED``, ``FE``."""
    value = _clean(text).strip()
    if not value or " " in value:
        return False
    letters = [ch for ch in value if ch.isalpha()]
    if len(letters) < 2 or len(letters) > 12:
        return False
    if looks_like_formula(value):
        return False
    uppers = sum(1 for ch in letters if ch.isupper())
    if uppers < 2 or uppers / len(letters) < 0.6:
        return False
    # allow internal capitals, a trailing plural "s" and separators ("4Cl-BZS", "PeLEDs")
    return all(ch.isalpha() or ch.isdigit() or ch in "-+/" for ch in value)


def is_instance_label(label: str) -> bool:
    """Paper-scoped experiment instance rather than a professional concept.

    ``control device``, ``device A``, ``4Cl-BZS treated device``, ``film`` are instances:
    they belong to one paper and must not become global hubs.
    """
    value = _clean(label).lower()
    if not value:
        return False
    if re.search(r"\b(control|reference|pristine|treated|annealed|unannealed)\b", value) and re.search(
            r"\b(device|cell|film|sample|wafer|stack|diode)\b", value):
        return True
    if re.fullmatch(r"(?:the )?(?:device|cell|film|sample|wafer|substrate)\s*[a-z0-9-]*", value):
        return True
    if re.fullmatch(r"(?:sample|device|film)\s*[#\w.-]*\d+[a-z]?", value):
        return True
    return False


_SYMBOL_RE = re.compile(r"^[A-Za-zΑ-Ωα-ω][′'″]?$")
_ROMAN_RE = re.compile(r"^[IVX]{1,4}$")
_INSTRUMENT_RE = re.compile(r"^[A-Z][A-Za-z0-9\-+.]+(?:\s+[A-Za-z0-9\-+.]+){0,3}\s+\d{2,}[A-Za-z]*$")
_VERB_RE = re.compile(
    r"(?i)\b(is|are|was|were|has|have|had|can|could|may|might|shows?|exhibits?|enables?|improves?|"
    r"leads?|results?|causes?|allows?|provides?|remains?|becomes?|occurs?|exists?)\b")
_COMPARATIVE_RE = re.compile(
    r"(?i)^(more|less|higher|lower|larger|smaller|greater|efficient|considerably|significantly|severe|"
    r"poor|high|low|enhanced|improved|reduced|increased|decreased|substantial|stronger|weaker|faster|"
    r"slower|better|worse|comparable)\b")


def is_symbol_fragment(label: str) -> bool:
    """Single letters, roman numerals and symbol fragments produced by formula parsing."""
    value = _clean(label).strip()
    if not value:
        return True
    if _SYMBOL_RE.fullmatch(value) or _ROMAN_RE.fullmatch(value):
        return True
    return value in {"ηPL", "Eb", "VI"}


def label_quality(label: str) -> str:
    """Rough quality class of a v2 label: ``clean``, ``fragment``, ``instrument``, ``symbol``.

    ``fragment`` means the label is a sentence fragment (verb, comparative, trailing
    preposition, or more than seven words) rather than a term. Fragments are still kept in
    the concept layer -- deleting data is not a quality fix -- but they are flagged and the
    retrieval layer hides them by default.
    """
    value = _clean(label).strip()
    if not value or is_symbol_fragment(value):
        return "symbol"
    if _INSTRUMENT_RE.match(value):
        return "instrument"
    words = value.split()
    lowered = value.lower()
    if (len(words) > 7 or _VERB_RE.search(lowered) or " than " in f" {lowered} "
            or _COMPARATIVE_RE.match(lowered)
            or re.search(r"(?i)\b(of|by|on|for|with|in|at|from|to|and|or)$", lowered)):
        return "fragment"
    return "clean"


# --------------------------------------------------------------------------- #
# Abbreviation mining
# --------------------------------------------------------------------------- #
_PAREN_RE = re.compile(r"([A-Za-z0-9][^()]{2,80}?)\s*\(([^()]{1,40})\)")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

#: Leading words that belong to the sentence, not to the expansion ("We used density
#: functional theory" -> "density functional theory").
_EXPANSION_STOP_PREFIX = frozenset(
    """a an the this that these those our their its we i they he she it is are was were be
    been being has have had uses use used using prepares prepare prepared prepared deposits
    deposit deposited grows grow grown measures measure measured obtains obtain obtained
    synthesizes synthesize synthesized forms form formed shows show shown reports report
    reported employs employ employed via through by with of in on at from as and or than
    more less which where when while they're""".split()
)

#: Generic nouns that trail a proper term name without adding meaning.
_GENERIC_SUFFIX = ("procedure", "technique", "approach", "strategy", "route")


#: A parenthetical expansion must be a name phrase, not a clause: relative pronouns and
#: finite verbs mean the text before the parenthesis is not the expansion.
_EXPANSION_CLAUSE_RE = re.compile(
    r"(?i)\b(which|that|where|whose|who|is|are|was|were|has|have|effects?|affects?|enables?|"
    r"shows?|exhibits?|causes?|limits?|improves?|reduces?|increases?)\b")


def _trim_expansion(words: list[str]) -> str:
    """Drop leading sentence words and trailing clause junk from an expansion.

    ``"... single photon detectors, and focal plane arrays (FPAs)"`` must yield
    ``focal plane arrays``: the expansion of an abbreviation is the noun phrase right before
    the parenthesis, not the whole list.
    """
    while words and words[0].strip(".,;:").lower() in _EXPANSION_STOP_PREFIX:
        words = words[1:]
    text = " ".join(words)
    # keep the last coordinate of a comma list ("carbides, nitrides (X)" -> "nitrides")
    parts = [part.strip() for part in re.split(r"[,;]", text) if part.strip()]
    if len(parts) > 1:
        text = parts[-1]
    text = re.sub(r"(?i)^(and|or)\s+", "", text).strip()
    while len(text.split()) > 2 and text.split()[-1].strip(".,;:").lower() in _GENERIC_SUFFIX:
        text = " ".join(text.split()[:-1])
    return text.strip(" .,;:")


def _plausible_abbreviation(token: str) -> bool:
    """A parenthetical may be an abbreviation: short, no spaces, at least one capital."""
    token = token.strip().strip(".,;:")
    if not token or " " in token:
        return False
    letters = [ch for ch in token if ch.isalpha()]
    if len(letters) < 2 or len(letters) > 12:
        return False
    return any(ch.isupper() for ch in letters)


def extract_parenthetical_aliases(text: str) -> list[dict]:
    """Mine ``full name (ABBR)`` pairs from running text.

    Each hit is returned with the sentence it came from so the alias can be reviewed and,
    because abbreviations are ambiguous across a corpus, only ever trusted inside the
    paper where the expansion was written.
    """
    hits: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for sentence in _SENTENCE_SPLIT_RE.split(_clean(text)):
        for match in _PAREN_RE.finditer(sentence):
            full = _trim_expansion(match.group(1).split())
            abbr = match.group(2).strip(" .;,")
            if not full or not _plausible_abbreviation(abbr):
                continue
            # "full" must look like a name phrase, not a clause.
            if len(full.split()) > 8 or re.search(r"[.;!?]$", full):
                continue
            if _EXPANSION_CLAUSE_RE.search(full):
                continue
            if is_abbreviation(full) and compact_key(full) != compact_key(abbr):
                continue
            key = (compact_key(abbr), compact_key(full))
            if key in seen:
                continue
            seen.add(key)
            hits.append({
                "alias": abbr,
                "expansion": full,
                "evidence": sentence.strip()[:300],
                "kind": "parenthetical",
            })
    return hits


def abbreviation_expansions(aliases: list[dict]) -> dict[str, str]:
    """Map ``ABBR -> expansion`` for one paper, first definition wins."""
    table: dict[str, str] = {}
    for item in aliases:
        abbr, expansion = str(item.get("alias", "")), str(item.get("expansion", ""))
        if not abbr or not expansion:
            continue
        table.setdefault(abbr, expansion)
    return table


# --------------------------------------------------------------------------- #
# Type classification
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class TypeRule:
    name: str
    pattern: re.Pattern[str]
    type: str


#: Head noun -> concept type. The head noun of a noun phrase carries the category
#: ("conductivity modulation" is a mechanism even though "conductivity" is a property;
#: "atomic layer deposition" is a process even though it contains "layer"). Multi-word
#: heads ("band maximum") are matched first.
HEAD_TYPE_INDEX: dict[str, str] = {
    # devices
    "cell": "device", "cells": "device", "device": "device", "devices": "device",
    "diode": "device", "diodes": "device", "photodetector": "device", "photodetectors": "device",
    "photodiode": "device", "photodiodes": "device", "detector": "device", "detectors": "device",
    "led": "device", "leds": "device", "sensor": "device", "sensors": "device",
    "array": "device", "arrays": "device", "transistor": "device", "transistors": "device",
    "memory": "device", "memories": "device", "modulator": "device", "modulators": "device",
    "capacitor": "device", "capacitors": "device", "panel": "device", "panels": "device",
    "module": "device", "modules": "device", "tandem": "device", "tandems": "device",
    # components / parts
    "layer": "component", "layers": "component", "contact": "component", "contacts": "component",
    "absorber": "component", "absorbers": "component", "electrode": "component",
    "electrodes": "component", "stack": "component", "stacks": "component",
    "substrate": "component", "substrates": "component", "spacer": "component",
    "window": "component", "windows": "component", "interface": "interface",
    "interfaces": "interface", "junction": "structure", "junctions": "structure",
    # defects
    "defect": "defect", "defects": "defect", "vacancy": "defect", "vacancies": "defect",
    "antisite": "defect", "antisites": "defect", "trap": "defect", "traps": "defect",
    "impurity": "defect", "impurities": "defect",
    # properties / quantities
    "coefficient": "property", "coefficients": "property", "energy": "property",
    "energies": "property", "yield": "property", "yields": "property", "voltage": "property",
    "voltages": "property", "current": "property", "currents": "property",
    "efficiency": "property", "efficiencies": "property", "factor": "property",
    "factors": "property", "mobility": "property", "mobilities": "property",
    "conductivity": "property", "conductivities": "property", "resistance": "property",
    "resistances": "property", "resistivity": "property", "temperature": "property",
    "temperatures": "property", "crystallinity": "property", "wettability": "property",
    "hysteresis": "property", "bandgap": "property", "thickness": "property",
    "permittivity": "property", "lifetime": "property", "absorption": "property",
    "transmittance": "property", "deficit": "property", "deficits": "property",
    "plqy": "property", "pce": "property", "eqe": "property", "ff": "property",
    "bv": "property", "responsivity": "property", "detectivity": "property",
    "density": "property", "ratio": "property", "index": "property", "constant": "property",
    "material": "material", "materials": "material",
    # mechanisms / phenomena
    "recombination": "mechanism", "transport": "mechanism", "confinement": "mechanism",
    "transfer": "mechanism", "modulation": "mechanism", "separation": "mechanism",
    "injection": "mechanism", "extraction": "mechanism", "polarization": "mechanism",
    "scattering": "mechanism", "tunneling": "mechanism", "thermalization": "mechanism",
    "generation": "mechanism", "diffusion": "mechanism", "degradation": "mechanism",
    "passivation": "mechanism", "kinetics": "mechanism", "reaction": "mechanism",
    "reactions": "mechanism", "emission": "mechanism", "loss": "mechanism", "losses": "mechanism",
    # structures
    "structure": "structure", "structures": "structure", "phase": "structure",
    "phases": "structure", "superlattice": "structure", "superlattices": "structure",
    "order": "structure", "ordering": "structure", "heterostructure": "structure",
    "heterostructures": "structure", "heterojunction": "structure", "heterojunctions": "structure",
    "solution": "structure", "solutions": "structure", "monolayer": "structure",
    "monolayers": "structure", "boundary": "structure", "boundaries": "structure",
    "disorder": "structure", "segregation": "structure", "stacking": "structure",
    "texture": "structure", "facet": "structure", "facets": "structure",
    "orientation": "structure", "morphology": "structure", "crystal": "structure",
    "crystals": "structure", "lattice": "structure", "arrangement": "structure",
    # characterization / calculation methods
    "theory": "characterization", "calculation": "characterization", "calculations": "characterization",
    "simulation": "characterization", "simulations": "characterization",
    "spectroscopy": "characterization", "diffraction": "characterization",
    "microscopy": "characterization", "metrology": "characterization", "measurement": "characterization",
    "measurements": "characterization", "characterization": "characterization",
    # processes
    "deposition": "process", "evaporation": "process", "exfoliation": "process",
    "annealing": "process", "doping": "process", "engineering": "process",
    "treatment": "process", "treatments": "process", "coating": "process",
    "synthesis": "process", "growth": "process", "etching": "process",
    "functionalization": "process", "purification": "process", "epitaxy": "process",
    "sputtering": "process", "printing": "process", "crystallization": "process",
    "exchange": "process", "ald": "process", "cvd": "process", "pvd": "process",
    # material classes
    "perovskite": "material_class", "perovskites": "material_class", "mxene": "material_class",
    "mxenes": "material_class", "carbide": "material_class", "carbides": "material_class",
    "nitride": "material_class", "nitrides": "material_class", "oxide": "material_class",
    "oxides": "material_class", "polymer": "material_class", "polymers": "material_class",
    "acid": "material_class", "acids": "material_class", "nanoparticle": "material_class",
    "nanoparticles": "material_class", "nanotube": "material_class", "nanotubes": "material_class",
    "nanocrystal": "material_class", "nanocrystals": "material_class",
    "dot": "material_class", "dots": "material_class", "semiconductor": "material_class",
    "semiconductors": "material_class", "metal": "material_class", "metals": "material_class",
    "alloy": "material_class", "alloys": "material_class", "dye": "material_class",
    "dyes": "material_class", "ligand": "material_class", "ligands": "material_class",
    "fullerene": "material_class", "fullerenes": "material_class",
    "dichalcogenide": "material_class", "dichalcogenides": "material_class",
    "halide": "material_class", "halides": "material_class", "salt": "material_class",
    "salts": "material_class", "dielectric": "material_class", "dielectrics": "material_class",
    "derivative": "material_class", "derivatives": "material_class",
    "compound": "material_class", "compounds": "material_class",
    "complementarity": "mechanism",
    "interaction": "mechanism", "interactions": "mechanism", "retention": "property",
    "stress": "property", "strain": "property", "psc": "device", "pscs": "device",
    "uniformity": "property", "shift": "property", "rate": "property", "rates": "property",
    "diffractometer": "characterization", "spectrometer": "characterization",
    "microscope": "characterization", "instrument": "characterization", "instruments": "characterization",
    # multi-word heads (matched before the single-word head)
    "matrix elements": "property", "band maximum": "property", "band minimum": "property",
    "molecular crystal": "material_class", "molecular crystals": "material_class",
    "quantum dot": "material_class", "quantum dots": "material_class",
    "solid solution": "structure", "solid solutions": "structure",
    "quantum well": "structure", "quantum wells": "structure",
    "grain boundary": "structure", "grain boundaries": "structure",
    "valence band": "property", "conduction band": "property",
}

#: Element names that turn "<metal> oxide/nitride/... " into a specific material
#: ("indium tin oxide") rather than a material class ("metal oxides").
_METAL_WORDS = frozenset(
    """aluminium aluminum antimony barium beryllium bismuth cadmium calcium cerium cesium
    chromium cobalt copper gallium germanium gold hafnium indium iridium iron lanthanum lead
    lithium magnesium manganese mercury molybdenum neodymium nickel niobium osmium palladium
    platinum potassium praseodymium rhenium rhodium rubidium ruthenium samarium scandium
    silver sodium strontium tantalum terbium thallium thorium tin titanium tungsten uranium
    vanadium ytterbium yttrium zinc zirconium""".split()
)

#: Specific substances whose head noun would otherwise read as a material class.
_MATERIAL_WORDS = frozenset({"graphene", "graphite", "diamond", "silicon", "germanium", "tellurium"})

_TYPE_RULES: tuple[TypeRule, ...] = (
    TypeRule("device", re.compile(
        r"(?i)\b(solar cells?|photovoltaics?|photodetectors?|photodiodes?|detectors?|leds?|oled|"
        r"sensors?|arrays?|transistors?|memor(?:y|ies)|modulators?|diodes?|devices?|"
        r"tandems?|cells?|panels?|modules?|capacitors?|emitters?)\b"), "device"),
    TypeRule("component", re.compile(
        r"(?i)\b(layers?|contacts?|absorbers?|electrodes?|gate stacks?|spacers?|"
        r"substrates?|transport layers?|buffer layers?|windows?)\b"), "component"),
    TypeRule("defect", re.compile(
        r"(?i)\b(defects?|vacanc(?:y|ies)|antisites?|impurities|traps?|dangling bonds?|"
        r"undercoordinated\b|interstitials?|pinholes?)\b"), "defect"),
    TypeRule("property", re.compile(
        r"(?i)\b(mobility|conductivity|resistivity|permittivity|crystallinity|wettability|"
        r"band ?gaps?|transmittance|detectivity|responsivity|plqy|vbm|cbm|pce|eqe)\b"),
        "property"),
    TypeRule("mechanism", re.compile(
        r"(?i)\b(recombination|confinement|thermalization|polarization|scattering|tunneling|"
        r"modulation|transfer|injection|extraction|diffusion|segregation)\b"), "mechanism"),
    TypeRule("structure", re.compile(
        r"(?i)\b(superlattices?|heterostructures?|quantum[- ]wells?|solid solutions?|monolayers?|"
        r"grain boundar(?:y|ies)|polymorphs?|textures?|facets?|orientations?|morpholog(?:y|ies)|"
        r"heterojunctions?|lattices?)\b"), "structure"),
    TypeRule("characterization", re.compile(
        r"(?i)\b(density functional theory|dft|first[- ]principles?|simulations?|calculations?|"
        r"spectroscop(?:y|ies)|diffraction|xrd|xps|ups|sem|tem|afm|stm|ellipsometry|"
        r"characterizations?|microscop(?:y|ies)|profilometry)\b"), "characterization"),
    TypeRule("process", re.compile(
        r"(?i)\b(deposition|evaporation|exfoliation|exfoliating|annealing|doping|engineering|"
        r"treatments?|coating|synthesis|growth|etching|passivation|functionalization|"
        r"purification|epitaxy|sputtering|spin[- ]coating|printing|crystallization|"
        r"ligand exchange)\b"), "process"),
    TypeRule("material_class", re.compile(
        r"(?i)\b(perovskites?|mxenes?|carbides?|nitrides?|oxides?|polymers?|acids?|"
        r"nanoparticles?|nanotubes?|nanocrystals?|quantum dots?|semiconductors?|"
        r"alloys?|dyes?|ligands?|fullerenes?|dichalcogenides?|tmdcs?|"
        r"two-dimensional materials?|2d materials?|halides?|salts?|dielectrics?)\b"),
        "material_class"),
)


def _head_tokens(label: str) -> list[str]:
    """Lower-case word tokens; hyphens split so "solution-coating" exposes "coating"."""
    return re.findall(r"[a-z0-9]+", _clean(label).lower())


def _head_type(label: str) -> tuple[str, str] | None:
    """Type carried by the head noun of the phrase, if any."""
    tokens = _head_tokens(label)
    if not tokens:
        return None
    for size in (3, 2):
        if len(tokens) >= size:
            head = " ".join(tokens[-size:])
            if head in HEAD_TYPE_INDEX:
                return HEAD_TYPE_INDEX[head], f"head:{head}"
    last = tokens[-1]
    if last in HEAD_TYPE_INDEX:
        return HEAD_TYPE_INDEX[last], f"head:{last}"
    return None


def classify_type(label: str) -> tuple[str, str]:
    """Classify a surface label deterministically; returns ``(type, rule)``.

    Resolution order: chemical formula -> head noun -> phrase pattern -> fallback
    ``material``. The head noun wins because English noun phrases are head-final, which is
    what keeps "atomic layer deposition" a process and "conductivity modulation" a mechanism.
    """
    value = _clean(label)
    if not value:
        return "material", "empty"
    if formula_identity(value):
        return "material", "formula"
    if _INSTRUMENT_RE.match(value):
        return "characterization", "instrument"
    head = _head_type(value)
    if head:
        kind, rule = head
        tokens = _head_tokens(value)
        if kind == "material_class" and tokens and tokens[-1] in {"oxide", "oxides", "nitride", "nitrides",
                                                                 "carbide", "carbides", "sulfide", "sulfides",
                                                                 "halide", "halides"}:
            if any(token in _METAL_WORDS for token in tokens[:-1]):
                return "material", "head:" + tokens[-1] + "+metal"
        return kind, rule
    tokens = _head_tokens(value)
    if tokens and tokens[-1] in _MATERIAL_WORDS:
        return "material", f"substance:{tokens[-1]}"
    if any(token in _MATERIAL_WORDS for token in tokens):
        return "material", "substance"
    for rule in _TYPE_RULES:
        if rule.pattern.search(value):
            return rule.type, rule.name
    return "material", "default-material"


@dataclass
class TypeResolution:
    """Outcome of reconciling observed v2 types with the concept-layer classifier."""

    type: str
    status: str           # consistent | conflict-resolved | unclassified
    observed: list[str] = field(default_factory=list)
    reason: str = ""
    conflicts: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"type": self.type, "status": self.status, "observed": self.observed,
                "reason": self.reason, "conflicts": self.conflicts}


def resolve_type(label: str, observed_types: list[str] | None = None,
                 expansion: str | None = None) -> TypeResolution:
    """Pick one concept type, reporting -- never hiding -- disagreements.

    ``expansion`` is the paper-scoped long form of an abbreviation; classification uses it
    so ``MOS`` (metal oxide semiconductors) is a material class rather than the element
    sequence M-O-S. ``observed_types`` are the types v2 assigned; they are evidence about
    the concept but they do not overrule the rules by frequency.
    """
    observed = [str(t).strip().lower() for t in (observed_types or []) if str(t).strip()]
    mapped = [V2_TYPE_MAP[t] for t in observed if V2_TYPE_MAP.get(t)]
    target = classify_type(expansion or label)
    kind, rule = target
    families = {TYPE_FAMILIES[t] for t in mapped}
    conflicts: list[str] = []
    if observed and all(v is None for v in (V2_TYPE_MAP.get(t) for t in observed)):
        return TypeResolution(kind, "instance_only", observed,
                              f"v2 emitted only instance types ({', '.join(observed)}); classified as {kind} "
                              f"by rule {rule}", [f"instance-type-only:{','.join(observed)}"])
    if mapped and kind not in mapped:
        if label_quality(expansion or label) == "fragment":
            # A sentence fragment has no reliable head noun; the type is recorded as
            # pending instead of pretending the rule resolved it.
            return TypeResolution(kind, "type_pending", observed,
                                  f"fragment label; rule {rule} vs v2 {sorted(set(mapped))}",
                                  [f"pending:v2={'/'.join(sorted(set(mapped)))} rule={kind}"])
        if kind == "material" and rule == "default-material":
            # No rule matched the label. Rather than force a blind default, keep the type
            # v2 mostly used and mark the record for review -- an unknown label is a
            # definition gap, not a conflict the rules can overrule.
            consensus = Counter(mapped).most_common(1)[0][0]
            return TypeResolution(consensus, "v2_fallback", observed,
                                  f"no rule matched; kept v2 type {consensus}", [])
        conflicts.append(f"v2={'/'.join(sorted(set(mapped)))} rule={kind} ({rule})")
        return TypeResolution(kind, "conflict_resolved", observed,
                              f"rule {rule} wins over v2 types {sorted(set(mapped))}", conflicts)
    if mapped and len(set(mapped)) > 1:
        conflicts.append(f"v2 types disagree: {'/'.join(sorted(set(mapped)))}")
        return TypeResolution(kind, "conflict_resolved", observed,
                              f"v2 types disagree; kept {kind} (rule {rule})", conflicts)
    if not mapped and families:
        return TypeResolution(kind, "instance_only", observed,
                              f"v2 type family {sorted(families)} mapped to {kind}", conflicts)
    return TypeResolution(kind, "consistent", observed, f"rule {rule}", conflicts)


# --------------------------------------------------------------------------- #
# Attribute phrases and composite mentions
# --------------------------------------------------------------------------- #
_WRAPPER_RE = re.compile(
    r"(?i)^(?:the\s+)?(?:development|advances?|progress|recent progress|study|application|"
    r"research|review|use|improvement|effect|role|investigation|understanding|prospects?)"
    r"\s+(?:of|on|in)\s+(.+)$")
_CHANGE_RE = re.compile(
    r"(?i)^(?P<head>.+?)\s+(?P<change>enhanced|improved|increased|reduced|decreased|boosted|"
    r"suppressed|diminished|grown|promoted)\s+(?P<prep>by|to|from|after|upon|with|via|through)\s+"
    r"(?P<detail>.+)$")
_CONDITION_RE = re.compile(
    r"(?i)^(?P<head>.+?)\s+(?P<cond>under|at|during|after|before|below|above|near)\s+(?P<detail>.+)$")
_OF_RE = re.compile(r"(?i)^(?P<head>.+?)\s+of\s+(?:the\s+)?(?P<detail>.+)$")
_PP_RE = re.compile(
    r"(?i)^(?P<head>[A-Za-z0-9][^,;:]{2,80}?)\s+"
    r"(?P<prep>by|on|for|with|in|at|from|than|via|through|between|and|or)\s+(?P<detail>.+)$")
_COMPOSITE_RE = re.compile(
    r"(?i)^(?P<modifier>.+?)\s+(?:modified|decorated|doped|coated|functionalized)\s+(?P<target>.+)$")
_GERUND_RE = re.compile(
    r"(?i)^(?P<verb>exfoliating|delaminating|etching|annealing|coating|depositing|treating|"
    r"passivating|doping|growing|synthesizing|purifying)\s+(?:the\s+)?(?P<object>.+)$")
_GERUND_NOUN = {
    "exfoliating": "exfoliation", "delaminating": "delamination", "etching": "etching",
    "annealing": "annealing", "coating": "coating", "depositing": "deposition",
    "treating": "treatment", "passivating": "passivation", "doping": "doping",
    "growing": "growth", "synthesizing": "synthesis", "purifying": "purification",
}
_MATERIAL_ENDING_RE = re.compile(r"(?i)\b(molecules?|powders?|films?|samples?|particles?|crystals?|ions?|atoms?)[.,;:]?$")
_GENERIC_SUFFIX_RE = re.compile(
    r"(?i)^(?P<head>.+?)\s+(?P<suffix>procedure|technique|approach|strategy|route)$")

#: Words that make a phrase an attribute sentence rather than a concept on their own.
CONDITION_WORDS = ("under", "at", "during", "after", "before", "below", "above", "near")


@dataclass
class PhraseSplit:
    """Result of separating a long mention into head concept plus attached detail."""

    kind: str                 # concept | attribute_phrase | composite | instance
    head: str
    wrapper: str = ""
    change: str = ""
    prep: str = ""
    detail: str = ""
    condition: str = ""
    modifiers: list[str] = field(default_factory=list)
    reason: str = ""

    def as_dict(self) -> dict:
        return {"kind": self.kind, "head": self.head, "wrapper": self.wrapper,
                "change": self.change, "prep": self.prep, "detail": self.detail,
                "condition": self.condition, "modifiers": self.modifiers, "reason": self.reason}


#: Nominalisations that describe a change, not a concept: "reduction of operating temperature"
#: names the change and the concept separately ("reduction" + operating temperature).
_NOMINAL_CHANGE_WORDS = frozenset(
    {"release", "reduction", "increase", "decrease", "improvement", "enhancement", "formation",
     "creation", "absence", "presence", "use", "effect", "role", "suppression", "growth",
     "development", "evolution", "variation", "change", "dependence"})

#: Leading comparative / evaluative adjectives that belong to the fact, not the concept.
_COMPARATIVE_WORDS = frozenset(
    {"more", "less", "higher", "lower", "larger", "smaller", "greater", "efficient", "considerable",
     "considerably", "significantly", "severe", "poor", "high", "low", "enhanced", "improved",
     "reduced", "increased", "decreased", "substantial", "strong", "stronger", "weak", "weaker",
     "faster", "slower", "better", "worse", "comparable", "excellent", "superior", "enhancement"})


def _strip_evaluative(head: str) -> tuple[str, list[str]]:
    """Remove leading comparative adjectives from a head phrase."""
    words = head.split()
    modifiers = []
    while words and words[0].strip(".,;:").lower() in _COMPARATIVE_WORDS:
        modifiers.append(words.pop(0))
    return (" ".join(words).strip(), modifiers)


def split_attribute_phrase(label: str) -> PhraseSplit:
    """Split a long label into a head concept and the detail that belongs in a fact.

    The split follows the four cases observed in the review: a wrapped mention
    ("development of ..."), a changed property ("... enhanced by up to a factor of two"),
    a conditioned mention ("... under mild annealing conditions") and a composite mention
    ("organic polymers modified MOS"). Anything that is already a clean concept is returned
    unchanged; composite mentions are *kept* as mentions and linked to their parts instead
    of being truncated.
    """
    value = _clean(label)
    if not value:
        return PhraseSplit("concept", "", reason="empty")

    match = _WRAPPER_RE.match(value)
    if match:
        head = match.group(1).strip()
        split = split_attribute_phrase(head)
        split.wrapper = match.group(0)[: match.end(1) - len(head)].strip()
        split.kind = "attribute_phrase" if split.kind == "concept" else split.kind
        split.reason = "wrapper phrase (development of / progress on ...) is not part of the concept"
        return split

    match = _CHANGE_RE.match(value)
    if match:
        head = match.group("head").strip()
        return PhraseSplit(
            "attribute_phrase", head, change=match.group("change").lower(),
            prep=match.group("prep").lower(), detail=match.group("detail").strip(),
            reason="a change and its magnitude/condition belong to a fact, not to the concept name")

    match = _CONDITION_RE.match(value)
    if match:
        head = match.group("head").strip()
        return PhraseSplit(
            "attribute_phrase", head, condition=f"{match.group('cond').lower()} {match.group('detail').strip()}",
            detail=match.group("detail").strip(),
            reason="a stated condition belongs to the fact, not to the concept name")

    match = _COMPOSITE_RE.match(value)
    if match:
        modifier = match.group("modifier").strip()
        target = match.group("target").strip()
        return PhraseSplit(
            "composite", target, modifiers=[modifier], detail=target,
            reason="composite mention: keep it as a mention and link modifier -> target")

    match = _GERUND_RE.match(value)
    if match:
        verb = match.group("verb").lower()
        return PhraseSplit(
            "attribute_phrase", _GERUND_NOUN.get(verb, verb), change=verb,
            detail=match.group("object").strip(),
            reason="an action phrase names a process; keep the action and its object as fact detail")

    match = _PP_RE.match(value)
    if match:
        head = match.group("head").strip()
        head, modifiers = _strip_evaluative(head)
        if len(head.split()) >= 2 and not re.search(r"(?i)\b(of|by|on|for|with|in|at|from|to|and|or)$", head):
            # the head itself may still carry a form word ("SiC film on Si sample")
            inner = split_attribute_phrase(head)
            if inner.kind != "concept" and inner.head and inner.head != head:
                head = inner.head
            return PhraseSplit(
                "attribute_phrase", head, prep=match.group("prep").lower(),
                detail=match.group("detail").strip(), modifiers=modifiers,
                reason="a trailing prepositional phrase qualifies the mention; the head is the concept")

    match = _GENERIC_SUFFIX_RE.match(value)
    if match:
        return PhraseSplit(
            "attribute_phrase", match.group("head"), detail=match.group("suffix"),
            reason="a generic noun (procedure/technique) is not part of the concept name")

    match = _OF_RE.match(value)
    if match:
        head = match.group("head").strip()
        detail = match.group("detail").strip()
        if head.split()[0].lower() in _NOMINAL_CHANGE_WORDS:
            inner = split_attribute_phrase(detail)
            return PhraseSplit(
                "attribute_phrase", inner.head or detail, change=head.lower(),
                detail=inner.detail or detail, modifiers=inner.modifiers,
                reason="the nominalisation names a change; the concept is what is changed")
        head, modifiers = _strip_evaluative(head)
        if head and len(head.split()) <= 5:
            return PhraseSplit(
                "attribute_phrase", head, detail=detail, modifiers=modifiers,
                reason="possessive 'of' phrase qualifies the mention; the concept is the head")

    match = _MATERIAL_ENDING_RE.search(value)
    if match and len(value.split()) > 1:
        head, modifiers = _strip_evaluative(value[: match.start()].strip())
        if head:
            return PhraseSplit(
                "instance", head, detail=match.group(1).lower(), modifiers=modifiers,
                reason="material form word (molecules/films/powder) denotes an instance of the material")

    return PhraseSplit("concept", value, reason="clean concept label")


# --------------------------------------------------------------------------- #
# Relation families and direction
# --------------------------------------------------------------------------- #
RELATION_FAMILIES: dict[str, tuple[str, ...]] = {
    "taxonomy": ("is a", "is an", "part of", "has formula", "belongs to", "subset of", "kind of"),
    "composition": ("composed of", "consists of", "contains", "made of", "has element",
                    "doped with", "alloyed with", "mixture of"),
    "structure": ("has structure", "has phase", "crystallizes in", "exhibits structure",
                  "stacked with", "has layer", "has ordering"),
    "process": ("synthesized by", "deposited by", "grown by", "fabricated via", "prepared by",
                "annealed at", "annealed for", "treated with", "passivated by", "exfoliated by",
                "coated by", "formed by"),
    "characterization": ("characterized by", "measured by", "calculated by", "simulated by",
                         "analyzed by", "computed by", "modeled by"),
    "effect": ("improves", "limits", "enables", "causes", "induces", "suppresses", "enhances",
               "exhibits", "achieves", "retains",
               "reduces", "increases", "decreases", "leads to", "results in", "produces",
               "originates from", "attributed to", "drives", "promotes", "inhibits",
               "prevents", "regulates", "boosts", "degrades", "eliminates", "passivates",
               "stabilizes", "destabilizes", "modulates", "accelerates", "slows"),
    "application": ("used in", "used as", "applied in", "acts as", "employed in", "serves as",
                    "suitable for", "utilized in"),
    "phase_transition": ("undergoes transition", "undergoes phase transition", "transforms to",
                         "converts to", "phase transition to"),
    "dependency": ("depends on", "relies on", "determined by", "governed by"),
}

PREDICATE_FAMILY: dict[str, str] = {
    predicate: family for family, predicates in RELATION_FAMILIES.items() for predicate in predicates
}


def relation_family(predicate: str) -> str:
    """Map a predicate onto one of the relation families, ``other`` when unknown."""
    value = _SPACE_RE.sub(" ", str(predicate or "").strip().lower())
    if value in PREDICATE_FAMILY:
        return PREDICATE_FAMILY[value]
    for family, predicates in RELATION_FAMILIES.items():
        for candidate in predicates:
            if value.startswith(candidate):
                return family
    return "other"


@dataclass
class DirectionCheck:
    """Causal sanity of one relation, with the reason a reviewer needs."""

    ok: bool
    issue: str = ""
    canonical_direction: str = ""

    def as_dict(self) -> dict:
        return {"ok": self.ok, "issue": self.issue, "canonical_direction": self.canonical_direction}


#: Predicates that state a cause *behind* the subject ("X is attributed to Y"): the subject
#: is legitimately the observed effect, so a property -> mechanism direction is correct.
REVERSE_CAUSAL_PREDICATES = frozenset({
    "attributed to", "originates from", "results from", "derives from", "caused by", "due to",
    "stems from", "arises from", "explained by", "ascribed to",
})


def relation_direction_check(subject_type: str, predicate: str, object_type: str) -> DirectionCheck:
    """Flag relations whose causal direction contradicts the entity types.

    A treatment or a mechanism may improve a property; a property does not improve a
    treatment. This is exactly the ``absorption coefficient -> improves -> cation disorder
    homogenization`` error from the review. Reverse-causal predicates ("attributed to",
    "originates from") are exempt: there the effect is the subject and the cause the object.
    A flagged edge is not silently reversed: the reviewer confirms it against the evidence.
    """
    family = relation_family(predicate)
    if family != "effect":
        return DirectionCheck(True)
    if _SPACE_RE.sub(" ", str(predicate or "").strip().lower()) in REVERSE_CAUSAL_PREDICATES:
        return DirectionCheck(True, canonical_direction="effect -> cause (reverse-causal predicate)")
    s_fam, o_fam = TYPE_FAMILIES.get(subject_type, ""), TYPE_FAMILIES.get(object_type, "")
    if s_fam in _CAUSAL_FAMILIES and o_fam == _QUANTITY_FAMILY:
        return DirectionCheck(True, canonical_direction="process/mechanism -> property")
    if s_fam == _QUANTITY_FAMILY and o_fam in _CAUSAL_FAMILIES:
        return DirectionCheck(
            False,
            issue="a quantity is written as the cause of a process; the process most likely acts on the quantity",
            canonical_direction="process/mechanism -> property")
    if s_fam == _QUANTITY_FAMILY and o_fam == _QUANTITY_FAMILY:
        return DirectionCheck(True, canonical_direction="property -> property (keep verbatim)")
    return DirectionCheck(True, canonical_direction="unconstrained")


# --------------------------------------------------------------------------- #
# Evidence qualifiers
# --------------------------------------------------------------------------- #
_NEGATION_RE = re.compile(r"(?i)\b(?:not|no|never|without|neither|nor|cannot|can't|isn't|aren't)\b")
_HEDGE_RE = re.compile(
    r"(?i)\b(?:may|might|could|can|would|should|suggest(?:s|ed)?|indicat(?:e|es|ed)|"
    r"appear(?:s|ed)?|likely|unlikely|propos(?:e|es|ed)|hypothes(?:is|ize|ised)|expect(?:s|ed)?|"
    r"possible|possibly|probably|predict(?:s|ed)?)\b")


def evidence_qualifiers(evidence: str) -> tuple[str, str]:
    """Return ``(polarity, modality)`` read off the evidence sentence.

    ``polarity`` is ``negative`` when the sentence negates the relation, ``modality`` is
    ``hedged`` for may/could/suggest phrasing. Both default to ``unknown``/``asserted`` so a
    reviewer can tell "no qualifier found" from "no evidence text".
    """
    text = _clean(evidence or "")
    if not text:
        return "unknown", "asserted"
    polarity = "negative" if _NEGATION_RE.search(text) else "positive"
    modality = "hedged" if _HEDGE_RE.search(text) else "asserted"
    return polarity, modality


# --------------------------------------------------------------------------- #
# Concept registry
# --------------------------------------------------------------------------- #
def concept_id_for(concept_type: str, identity: str) -> str:
    """Stable concept id from type + identity key (not from the display label)."""
    digest = hashlib.sha1(f"{concept_type}:{identity}".encode("utf-8")).hexdigest()
    return "c-" + digest[:12]


def identity_key(label: str, concept_type: str, abbreviation_expansion: str | None = None) -> str:
    """Identity used for cross-paper merging.

    Chemical formulas merge by case-insensitive formula (stoichiometry and phase kept);
    plain names merge by compact key; abbreviations never merge on their own key -- they
    need a paper-scoped expansion, and even then the expansion is what is compared.
    """
    value = _clean(abbreviation_expansion or label)
    formula = formula_identity(value)
    if formula:
        return "formula:" + formula
    if is_abbreviation(label) and not abbreviation_expansion:
        return "abbrev:" + compact_key(label)
    return "name:" + singular_key(compact_key(value))


@dataclass
class ConceptRecord:
    """One professional concept with its aliases, papers and review status."""

    concept_id: str
    canonical_name: str
    type: str
    identity: str
    type_status: str = "consistent"
    type_reason: str = ""
    formula: str | None = None
    aliases: list[dict] = field(default_factory=list)
    surface_forms: dict[str, int] = field(default_factory=dict)
    papers: set[str] = field(default_factory=set)
    v2_types: set[str] = field(default_factory=set)
    conflicts: list[str] = field(default_factory=list)
    source: str = "v2_enriched"
    review_status: str = "machine"
    quality: str = "clean"
    language_labels: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "concept_id": self.concept_id,
            "canonical_name": self.canonical_name,
            "type": self.type,
            "type_status": self.type_status,
            "type_reason": self.type_reason,
            "formula": self.formula,
            "identity": self.identity,
            "quality": self.quality,
            "aliases": sorted(self.aliases, key=lambda a: (a.get("scope", ""), a.get("alias", ""))),
            "surface_forms": dict(sorted(self.surface_forms.items(), key=lambda kv: (-kv[1], kv[0]))),
            "papers": sorted(self.papers),
            "paper_count": len(self.papers),
            "mention_count": sum(self.surface_forms.values()),
            "v2_types": sorted(self.v2_types),
            "conflicts": self.conflicts,
            "language_labels": self.language_labels,
            "source": self.source,
            "review_status": self.review_status,
        }


class ConceptRegistry:
    """Collect labels from many papers and build the deduplicated concept layer.

    Merge safety is the whole point: a label joins an existing concept only when
    :func:`identity_key` matches *and* the two labels are mutually compatible. No substring
    matching, no shared-prefix merging, no lower-case abbreviation promotion.
    """

    def __init__(self) -> None:
        self._by_identity: dict[str, list[ConceptRecord]] = {}
        self._by_id: dict[str, ConceptRecord] = {}
        self.merges: list[dict] = []
        self.rejected_merges: list[dict] = []

    # -- internals -------------------------------------------------------
    def _find(self, identity: str, label: str) -> ConceptRecord | None:
        for record in self._by_identity.get(identity, []):
            if _merge_safe(record.canonical_name, label):
                return record
        return None

    # -- public ----------------------------------------------------------
    def add(self, paper_id: str, label: str, v2_types: list[str] | None = None,
            expansion: str | None = None, alias: str | None = None,
            evidence: str = "", review_status: str = "machine") -> ConceptRecord:
        """Register one occurrence of a label and return its concept record."""
        clean = _clean(label)
        if not clean:
            raise ValueError("empty label")
        resolution = resolve_type(clean, v2_types, expansion)
        identity = identity_key(clean, resolution.type, expansion)
        quality = label_quality(expansion or clean)
        record = self._find(identity, expansion or clean)
        if record is None:
            concept_type = resolution.type
            concept_id = concept_id_for(concept_type, identity)
            record = ConceptRecord(
                concept_id=concept_id,
                canonical_name=_display_name(expansion or clean),
                type=concept_type,
                identity=identity,
                type_status=resolution.status,
                type_reason=resolution.reason,
                formula=formula_identity(clean) or None,
                review_status=review_status,
                quality=quality,
            )
            self._by_identity.setdefault(identity, []).append(record)
            self._by_id[concept_id] = record
        else:
            if record.type != resolution.type:
                record.conflicts.append(
                    f"{paper_id}: type {resolution.type} disagrees with {record.type} for {clean!r}")
                self.rejected_merges.append({
                    "paper_id": paper_id, "label": clean, "concept_id": record.concept_id,
                    "reason": f"type mismatch {resolution.type} vs {record.type}"})
            if quality == "clean":
                record.quality = "clean"
            elif record.quality == "clean":
                pass
            elif quality != record.quality:
                record.quality = quality

        record.papers.add(paper_id)
        record.surface_forms[clean] = record.surface_forms.get(clean, 0) + 1
        record.v2_types.update(str(t).lower() for t in (v2_types or []) if t)
        if resolution.conflicts:
            record.conflicts.extend(f"{paper_id}: {c}" for c in resolution.conflicts)
        if alias and alias != clean:
            record.aliases.append({"alias": alias, "scope": "paper", "paper_id": paper_id,
                                   "kind": "abbreviation" if is_abbreviation(alias) else "surface",
                                   "verified": False, "evidence": evidence[:300]})
        if expansion and compact_key(expansion) != compact_key(clean):
            record.aliases.append({"alias": clean, "scope": "paper", "paper_id": paper_id,
                                   "kind": "abbreviation", "verified": True,
                                   "evidence": evidence[:300]})
        return record

    def get(self, concept_id: str) -> ConceptRecord | None:
        return self._by_id.get(concept_id)

    def find_label(self, label: str, paper_id: str | None = None) -> ConceptRecord | None:
        """Look a label up (paper-scoped first when a paper is given)."""
        clean = _clean(label)
        identity = identity_key(clean, classify_type(clean)[0])
        for record in self._by_identity.get(identity, []):
            if paper_id is None or paper_id in record.papers:
                if _merge_safe(record.canonical_name, clean):
                    return record
        return None

    @property
    def concepts(self) -> list[ConceptRecord]:
        return list(self._by_id.values())

    def to_list(self) -> list[dict]:
        return [record.as_dict() for record in sorted(self.concepts, key=lambda r: r.concept_id)]


def _display_name(label: str) -> str:
    """Display form: the author's spelling, without a trailing form word or wrapper."""
    value = _clean(label)
    match = _MATERIAL_ENDING_RE.search(value)
    if match and len(value.split()) > 1:
        value = value[: match.start()].strip()
    return value


def _merge_safe(existing: str, incoming: str) -> bool:
    """Two labels may share a concept only when the merge is provably safe.

    Safe: identical after normalisation; identical chemical identity; identical plain name.
    Unsafe (and therefore rejected): one label contained in the other, shared prefix only,
    or an abbreviation without an expansion.
    """
    a, b = _clean(existing), _clean(incoming)
    if a == b:
        return True
    fa, fb = formula_identity(a), formula_identity(b)
    if fa and fb:
        return fa == fb
    if is_abbreviation(a) or is_abbreviation(b):
        return False
    ca, cb = singular_key(compact_key(a)), singular_key(compact_key(b))
    if ca == cb:
        return True
    if ca in cb or cb in ca:
        return False  # substring / parent class -- never merged here
    return False
