"""Tests for the terminology layer (concepts, aliases, types, directions)."""
from knowledge_graph.terminology import (
    ConceptRegistry,
    classify_type,
    evidence_qualifiers,
    extract_parenthetical_aliases,
    formula_identity,
    is_abbreviation,
    is_instance_label,
    normalize_key,
    relation_direction_check,
    relation_family,
    resolve_type,
    split_attribute_phrase,
)


def test_normalize_key_keeps_phase_apart():
    assert normalize_key("α-FAPbI₃") != normalize_key("δ-FAPbI₃")
    assert normalize_key("HfO<sub>2</sub>") == normalize_key("hfo2")


def test_formula_identity_merges_case_but_not_stoichiometry():
    assert formula_identity("HfO₂") == formula_identity("HfO2") == "hfo2"
    assert formula_identity("Sb2O3") != formula_identity("Sb4O6")
    assert formula_identity("α-FAPbI3") == "alpha-fapbi3"
    assert formula_identity("δ-FAPbI3") == "delta-fapbi3"
    assert formula_identity("FAPbI3") == "fapbi3"
    # A defect site and an acronym are not formulas.
    assert formula_identity("Pb2+") is None
    assert formula_identity("FF") is None
    assert formula_identity("MOS") is None
    assert formula_identity("GaN") == "gan"


def test_is_abbreviation():
    assert is_abbreviation("TMDCs")
    assert is_abbreviation("APDs")
    assert is_abbreviation("STED")
    assert is_abbreviation("FE")
    assert not is_abbreviation("MXene")
    assert not is_abbreviation("Pb2+")
    assert not is_abbreviation("AgBiS2")


def test_is_instance_label():
    assert is_instance_label("control device")
    assert is_instance_label("4Cl-BZS treated device")
    assert is_instance_label("film")
    assert not is_instance_label("AgBiS2")


def test_classify_type_by_head_noun():
    cases = {
        "atomic layer deposition": "process",
        "conductivity modulation": "mechanism",
        "energy transfer": "mechanism",
        "one-step solution-coating": "process",
        "quasi-2D perovskites": "material_class",
        "avalanche photodiodes": "device",
        "electron transport layer": "component",
        "undercoordinated Pb2+": "defect",
        "valence band maximum": "property",
        "thermalization losses": "mechanism",
        "inorganic molecular crystal": "material_class",
        "indium tin oxide": "material",
        "graphene": "material",
        "ferroelectric order": "structure",
        "density functional theory": "characterization",
        "p-type doping": "process",
        "III-nitride": "material_class",
    }
    for label, expected in cases.items():
        assert classify_type(label)[0] == expected, label


def test_extract_parenthetical_aliases_trims_sentence_words():
    text = ("We used density functional theory (DFT) calculations. Transition metal "
            "dichalcogenides (TMDCs) were prepared by standard thermal evaporation deposition (STED).")
    hits = {(h["alias"], h["expansion"]) for h in extract_parenthetical_aliases(text)}
    assert ("DFT", "density functional theory") in hits
    assert ("TMDCs", "Transition metal dichalcogenides") in hits
    assert ("STED", "standard thermal evaporation deposition") in hits


def test_split_attribute_phrase_cases():
    split = split_attribute_phrase("absorption coefficient enhanced by up to a factor of two after annealing")
    assert split.kind == "attribute_phrase"
    assert split.head == "absorption coefficient"
    assert split.change == "enhanced"

    split = split_attribute_phrase("development of AlGaN-based solar-blind UV PDs")
    assert split.head == "AlGaN-based solar-blind UV PDs"
    assert split.wrapper == "development of"

    split = split_attribute_phrase("organic polymers modified MOS")
    assert split.kind == "composite"
    assert split.head == "MOS"
    assert split.modifiers == ["organic polymers"]

    split = split_attribute_phrase("exfoliating the 3D bulk to 2D planer structures")
    assert split.kind == "attribute_phrase"
    assert split.head == "exfoliation"

    split = split_attribute_phrase("Sb4O6 molecules")
    assert split.kind == "instance" and split.head == "Sb4O6"

    split = split_attribute_phrase("AgBiS2")
    assert split.kind == "concept"


def test_relation_family_and_direction():
    assert relation_family("improves") == "effect"
    assert relation_family("calculated by") == "characterization"
    assert relation_family("deposited by") == "process"

    bad = relation_direction_check("property", "improves", "process")
    assert not bad.ok and "quantity" in bad.issue
    assert relation_direction_check("mechanism", "improves", "property").ok
    assert relation_direction_check("process", "improves", "property").ok
    assert relation_direction_check("property", "is a", "property").ok


def test_evidence_qualifiers():
    assert evidence_qualifiers("The ligand may passivate the defect") == ("positive", "hedged")
    assert evidence_qualifiers("The device is not stable") == ("negative", "asserted")
    assert evidence_qualifiers("") == ("unknown", "asserted")


def test_resolve_type_reports_conflicts():
    result = resolve_type("quasi-2D perovskite", ["material", "material_class"])
    assert result.type == "material_class"
    assert result.status == "conflict_resolved"
    assert result.conflicts
    result = resolve_type("density functional theory", ["material"])
    assert result.type == "characterization"
    assert result.status == "conflict_resolved"


def test_concept_registry_merge_rules():
    reg = ConceptRegistry()
    hfo2_a = reg.add("p1", "HfO2", ["material"])
    hfo2_b = reg.add("p2", "HfO₂", ["material"])
    assert hfo2_a.concept_id == hfo2_b.concept_id
    assert len(hfo2_a.papers) == 2

    sb2o3 = reg.add("p1", "Sb2O3", ["material"])
    sb4o6 = reg.add("p1", "Sb4O6", ["material"])
    assert sb2o3.concept_id != sb4o6.concept_id

    alpha = reg.add("p1", "α-FAPbI3", ["material"])
    delta = reg.add("p1", "δ-FAPbI3", ["material"])
    assert alpha.concept_id != delta.concept_id

    # An abbreviation is paper-scoped: it becomes an alias of its expansion, never a global
    # synonym of an unrelated concept.
    fe = reg.add("p1", "FE", ["structure"], expansion="ferroelectric order", evidence="ferroelectric order (FE)")
    assert fe.canonical_name == "ferroelectric order"
    assert any(a["alias"] == "FE" and a["scope"] == "paper" for a in fe.aliases)
    assert reg.find_label("FE", paper_id="p2") is None

    # No substring merging: "device" never absorbs "control device".
    reg.add("p1", "device", ["device"])
    control = reg.add("p1", "control device", ["sample"])
    assert control.canonical_name == "control device"
    assert control.type == "device"  # classified by head noun, still its own concept
