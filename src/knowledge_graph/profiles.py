"""Domain profiles: what counts as an entity type, which predicates are allowed,
and which inference stages make sense for a discipline.

The generic profile reproduces the historical behaviour (9 entity types, free-form
predicates, all inference stages available). ``materials`` is the first scientific
profile: materials-science entity types, a controlled predicate list, no string-based
taxonomy, and no LLM relationship invention — facts must come from the text.
"""
from __future__ import annotations

from typing import Any

GENERIC_TYPES = ("person", "organization", "place", "event", "technology", "product", "work", "date", "concept")

MATERIALS_TYPES = (
    "material", "material_class", "sample", "structure", "device", "process", "condition",
    "property", "measurement", "characterization", "mechanism", "defect", "interface",
)

# Controlled predicate vocabulary. Keys are families, values are the canonical predicates;
# ``synonyms`` maps a verbatim model predicate onto a canonical one.
MATERIALS_PREDICATES: dict[str, list[str]] = {
    "taxonomy": ["is a", "part of", "has formula", "doped with", "alloyed with", "crystallizes in", "has phase"],
    "property": ["exhibits", "achieves", "has bandgap", "has efficiency", "has mobility",
                 "has measurement", "has thermal conductivity", "has conductivity",
                 "has carrier lifetime", "has detectivity", "has responsivity", "has eqe",
                 "has open-circuit voltage", "degrades after", "retains"],
    "process": ["synthesized by", "deposited by", "annealed at", "annealed for", "treated with",
                "passivated by", "measured by", "characterized by"],
    "device": ["used in", "composed of", "has layer", "stacked with"],
    "mechanism": ["improves", "limits", "enables", "originates from", "attributed to", "causes",
                  "depends on"],
    "observation": ["measures", "measured by"],
}

MATERIALS_PREDICATE_SET = {p for preds in MATERIALS_PREDICATES.values() for p in preds}

MATERIALS_SYNONYMS = {
    "enhances": "improves", "enhance": "improves", "boosts": "improves", "boost": "improves",
    "reduces": "limits", "reduce": "limits", "suppresses": "limits", "suppress": "limits",
    "based on": "composed of", "consists of": "composed of", "made of": "composed of",
    "is made by": "synthesized by", "fabricated by": "synthesized by", "prepared by": "synthesized by",
    "grown by": "deposited by", "deposited using": "deposited by",
    "analyzed by": "characterized by", "examined by": "characterized by",
}

PROFILES: dict[str, dict[str, Any]] = {
    "generic": {
        "name": "generic",
        "version": "1.0",
        "entity_types": GENERIC_TYPES,
        "predicates": None,          # free-form
        "prompt": "main",
        "force_inference_off": False,
        "build_observations": False,
        "preserve_case": False,
    },
    "materials": {
        "name": "materials",
        "version": "1.0",
        "entity_types": MATERIALS_TYPES,
        "predicates": MATERIALS_PREDICATE_SET,
        "prompt": "materials",
        "force_inference_off": True,   # no taxonomy / lexical / LLM bridge-hub-within
        "build_observations": True,    # numeric facts become observation nodes
        "preserve_case": True,         # CsPbI3 stays CsPbI3
        "synonyms": MATERIALS_SYNONYMS,
    },
}


def profile_name(config: dict[str, Any] | None) -> str:
    name = ((config or {}).get("profile") or {}).get("name") or "generic"
    return str(name).strip().lower()


def active_profile(config: dict[str, Any] | None) -> dict[str, Any]:
    return PROFILES.get(profile_name(config), PROFILES["generic"])


def entity_types(config: dict[str, Any] | None) -> tuple[str, ...]:
    return tuple(active_profile(config)["entity_types"])


def is_materials(config: dict[str, Any] | None) -> bool:
    return profile_name(config) == "materials"


def map_predicate(predicate: str, config: dict[str, Any] | None) -> tuple[str, bool]:
    """Return ``(canonical_predicate, unmapped)`` for the active profile."""
    prof = active_profile(config)
    allowed = prof.get("predicates")
    if not allowed:
        return predicate, False
    p = " ".join(str(predicate or "").lower().split())
    synonyms = prof.get("synonyms") or {}
    if p in synonyms:
        return synonyms[p], False
    if p in allowed:
        return p, False
    return predicate, True


def apply_profile_overrides(config: dict[str, Any]) -> dict[str, Any]:
    """Force profile-mandated settings (materials: every inference stage off)."""
    prof = active_profile(config)
    if prof.get("force_inference_off"):
        inf = config.setdefault("inference", {})
        inf.update({
            "enabled": True,          # the phase still runs; it just has nothing enabled
            "use_llm_for_inference": False,
            "llm_bridge": False,
            "llm_hub": False,
            "taxonomy": False,
            "lexical": False,
            "apply_transitive": False,
            "max_inferred_ratio": 0.0,
        })
    return config
