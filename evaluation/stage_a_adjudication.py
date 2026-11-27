"""Stage A semantic adjudication of the 96 reference terms and 36 reference relations.

The dossiers produced by :mod:`evaluation.stage_a_cases` are the evidence; the judgements
below are the review. Every record carries the verdict, the v2 label that represents the
concept (if any), what kind of miss it is when nothing represents it, the concrete repair,
and a reason a second reviewer can check against the dossier.

Verdicts (terms):
  correct_concept         a v2 node is this concept with an acceptable type
  correct_not_normalized  same concept, but only via an abbreviated / compound / over-long label
  granularity_different   only a parent class or a narrower variant exists
  misclassified           the concept exists but no acceptable type was assigned
  confirmed_missing       the concept is not represented in the graph at all
  pending                 cannot be decided from the dossier

Missing kinds (only for confirmed_missing):
  preprocess_loss         the source paragraph was removed before extraction (front/back matter)
  extracted_not_noded     the string occurs inside another label or in evidence, never as a node
  name_variant            a spelling variant the label rules did not match
  model_omission          the paragraph was extracted, the concept is absent from the output

Relation verdicts: supported / partially_supported / not_found / undetermined.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "evaluation" / "terminology_review_20261125" / "stage_a"
REFERENCE = ROOT / "evaluation" / "terminology_review_20261125" / "reference_and_comparison.json"

VERDICTS = ("correct_concept", "correct_not_normalized", "granularity_different",
            "misclassified", "confirmed_missing", "pending")


def T(verdict, v2_label="", missing_kind="", actions=(), type_issue="", reason=""):
    return {"verdict": verdict, "v2_label": v2_label, "missing_kind": missing_kind,
            "actions": list(actions), "type_issue": type_issue, "reason": reason}


# --------------------------------------------------------------------------- #
# Term adjudications
# --------------------------------------------------------------------------- #
TERMS: dict[str, dict[str, dict]] = {
    "001": {
        "4-chlorobenzenesulfonate": T(
            "correct_not_normalized", "4Cl-BZS", actions=["alias_split", "canonicalize"],
            reason="concept present, but only under the ligand abbreviation; the full name must be the "
                   "canonical label with 4Cl-BZS (and the hyphen/space variant) as paper-scoped aliases"),
        "benzenesulfonate": T(
            "correct_not_normalized", "BZS", actions=["alias_split", "canonicalize"],
            reason="same as the previous entry: BZS is an alias, and the four ring-substituted ligands "
                   "(BZS, 4CH3-BZS, 4Cl-BZS) must stay separate concepts"),
        "undercoordinated Pb2+": T(
            "correct_not_normalized", "undercoordinated Pb2+ ions", actions=["split_attribute", "canonicalize"],
            reason="v2 keeps the sentence fragment ('... ions', 'interaction with ...') as node names; the "
                   "defect concept is the head and the interaction belongs to the mechanism node"),
        "density functional theory": T(
            "confirmed_missing", "", "model_omission", ["targeted_reextract"],
            reason="the paragraph was extracted (chunk 2 produced 14 triples) and mentions DFT, but neither "
                   "the method name nor the abbreviation was ever emitted as a node or field"),
        "electron transport layer": T(
            "confirmed_missing", "", "extracted_not_noded", ["split_attribute", "targeted_reextract"],
            reason="ETL appears only inside the interface label 'top (ETL-facing) surface of the perovskite "
                   "film' and in evidence; the layer concept itself was never created"),
        "nonradiative recombination": T(
            "correct_not_normalized", "nonradiative recombination at the perovskite/CTL interface",
            actions=["split_attribute", "canonicalize"],
            reason="the mechanism is stored as two long variants (interface qualifier inside the name); the "
                   "head concept plus an interface qualifier is what a searcher needs"),
        "fill factor": T(
            "correct_concept", "fill factor", actions=["keep"],
            reason="clean property node; FF appears in measurements as a separate abbreviation and should be "
                   "registered as an alias"),
        "inverted perovskite solar cells": T(
            "granularity_different", "perovskite solar cells", actions=["add_edge", "type_fix"],
            reason="only the parent class (typed device *and* material_class) and sample-level 'pin PSC' "
                   "instances exist; the inverted/pin device concept is missing"),
    },
    "011": {
        "Ga2O3": T("correct_concept", "Ga2O3", actions=["keep"],
                   reason="correct material node; qualified forms (n-Ga2O3, Ga2O3 layer) should hang off it"),
        "NiOx": T("correct_not_normalized", "p-NiOx", actions=["alias_split", "canonicalize"],
                  reason="only the p-doped form is a node; the material concept NiOx needs the p- prefix as a "
                         "doping qualifier and 'p-NiOx' as a paper-scoped alias"),
        "GaN": T("confirmed_missing", "", "extracted_not_noded", ["targeted_reextract"],
                 reason="GaN is used in the text as a comparison baseline and appears inside the long property "
                       "label 'breaking the 1-D unipolar ... limit of GaN and SiC'; no GaN node exists"),
        "SiC": T("confirmed_missing", "", "extracted_not_noded", ["targeted_reextract"],
                 reason="same paragraph as GaN; SiC occurs only inside a property phrase and evidence, never as "
                       "a material node"),
        "heterojunction PN diodes": T("confirmed_missing", "", "extracted_not_noded", ["targeted_reextract"],
                                      reason="'Ga2O3 HJ PN diodes' appears in evidence and in device names, but "
                                             "the device concept 'heterojunction PN diode' was never created"),
        "conductivity modulation": T("correct_not_normalized", "conductivity modulation effect",
                                     actions=["split_attribute", "canonicalize"],
                                     reason="mechanism present as 'conductivity modulation effect' and 'hole "
                                            "injection and conductivity modulation'; the head concept should be "
                                            "one node, the qualifiers separate facts"),
        "specific on-resistance": T("correct_not_normalized", "Ron,sp", actions=["alias_split", "canonicalize"],
                                    type_issue="symbol-only label",
                                    reason="only the symbol Ron,sp is a node; the property needs its full name "
                                           "as canonical and the symbol as alias (the symbol also occurs as "
                                           "part of longer labels)"),
        "breakdown voltage": T("confirmed_missing", "", "extracted_not_noded", ["targeted_reextract"],
                               reason="BV appears only inside device labels such as 'diode with BV = 8.32 kV'; "
                                      "the property concept itself was never created"),
    },
    "021": {
        "quasi-2D perovskites": T("correct_concept", "quasi-2D perovskite", actions=["keep", "type_fix"],
                                  type_issue="material vs material_class",
                                  reason="the class node exists (singular); the type is split between material "
                                         "and material_class and must be fixed to material_class"),
        "quantum-well structure": T("correct_concept", "quantum-well structures", actions=["keep"],
                                    reason="clean structure node; the qualified variants (natural, "
                                           "self-assembled multi-) should be sub-structures"),
        "dielectric confinement": T("correct_concept", "dielectric confinement", actions=["keep", "type_fix"],
                                    type_issue="mechanism vs property",
                                    reason="node exists with conflicting types; the mechanism reading is the "
                                           "one the paper uses"),
        "quantum confinement": T("correct_not_normalized", "quantum- and dielectric-confinement effects",
                                 actions=["split_compound", "canonicalize"],
                                 reason="only the combined compound node exists; quantum confinement and "
                                       "dielectric confinement are separate mechanisms"),
        "exciton binding energy": T("correct_concept", "exciton binding energy", actions=["keep"],
                                    reason="clean property node with observation nodes attached"),
        "energy transfer": T("correct_concept", "energy transfer", actions=["keep", "type_fix"],
                             type_issue="mechanism/process/property",
                             reason="node exists but carries three types; the paper uses it as a mechanism"),
        "photoluminescence quantum yield": T("correct_concept", "photoluminescence quantum yield", actions=["keep"],
                                             reason="full name and PLQY are both nodes; they should be one "
                                                    "concept with PLQY as alias, not two nodes"),
        "perovskite LEDs": T("correct_not_normalized", "PeLED", actions=["alias_split", "canonicalize"],
                             reason="only the singular abbreviation 'PeLED' (plus generic LEDs and qualified "
                                    "variants) exists; the device concept needs its full name and PeLEDs alias"),
    },
    "023": {
        "AlGaN": T("correct_concept", "AlGaN", actions=["keep", "type_fix"],
                   type_issue="material vs material_class",
                   reason="material node exists; material_class is also recorded for the ternary alloy, which "
                          "is a type conflict to resolve"),
        "III-nitride": T("correct_not_normalized", "III-nitride material", actions=["canonicalize", "alias_split"],
                         reason="the class node carries the generic noun 'material'; 'Group-III nitride "
                                "semiconductors' is a second surface form that should map to the same concept"),
        "solar-blind ultraviolet photodetectors": T("granularity_different", "PDs", actions=["add_edge"],
                                                    reason="only the generic 'PDs' device and the process phrase "
                                                           "'development of AlGaN-based solar-blind UV PDs' exist; "
                                                           "the specific device concept is missing"),
        "focal plane arrays": T("correct_not_normalized", "FPAs", actions=["alias_split", "canonicalize"],
                                reason="only the abbreviation is a node; the full name appears in evidence and "
                                       "in 'AlGaN-based focal plane arrays (FPAs)'"),
        "metal-semiconductor-metal photodetectors": T(
            "confirmed_missing", "", "extracted_not_noded", ["targeted_reextract"],
            reason="MSM appears as 'MSM PD' and 'metal-semiconductor-metal (MSM) PD' in text and evidence but "
                   "no MSM device node exists"),
        "avalanche photodiodes": T("correct_not_normalized", "avalanche photodiodes (APDs)",
                                   actions=["alias_split"], reason="node exists with the abbreviation inside the "
                                                                  "label; APDs must become an alias, not part of the name"),
        "epitaxy": T("correct_not_normalized", "AlGaN epitaxy", actions=["canonicalize", "split_compound"],
                     reason="only qualified forms (AlGaN epitaxy, direct epitaxy, HT-AlN epitaxy) exist; the "
                            "generic process concept is missing as a node"),
        "p-type doping": T("correct_not_normalized", "polarization-induced p-type doping",
                           actions=["canonicalize", "type_fix"], type_issue="p-type recorded as property",
                           reason="the process appears only in qualified form; 'p-type' is separately a property "
                                  "node, mixing a process with its qualifier"),
    },
    "038": {
        "metal oxide semiconductors": T("correct_concept", "Metal oxide semiconductors", actions=["keep"],
                                        reason="clean class node with the MOS abbreviation as a second node; the "
                                               "two should be one concept"),
        "flexible room-temperature gas sensors": T("correct_not_normalized", "FRT gas sensors",
                                                   actions=["alias_split", "canonicalize"],
                                                   reason="only the abbreviation is a node"),
        "noble metal nanoparticles": T("correct_concept", "noble metal nanoparticles", actions=["keep"],
                                       reason="clean class node"),
        "organic polymers": T("correct_not_normalized", "organic polymers modified MOS",
                              actions=["split_composite"],
                              reason="the polymer concept only exists inside the composite mention 'organic "
                                     "polymers modified MOS'; keep the composite and add the standalone concept"),
        "carbon nanotubes": T("confirmed_missing", "", "extracted_not_noded", ["split_composite"],
                              reason="carbon nanotubes appear in the evidence of the composite 'carbon-based "
                                     "materials modified MOS' and in the body text, but never as a node"),
        "graphene derivatives": T("correct_concept", "graphene derivatives", actions=["keep", "type_fix"],
                                  type_issue="material vs material_class",
                                  reason="node exists; a family of derivatives is a material_class"),
        "transition metal dichalcogenides": T("correct_not_normalized",
                                              "two-dimensional transition metal dichalcogenides materials modified MOS",
                                              actions=["split_composite", "canonicalize"],
                                              reason="TMDCs only exist inside the composite mention; the class "
                                                     "concept itself is missing"),
        "operating temperature": T("correct_concept", "operating temperature", actions=["keep", "type_fix"],
                                   type_issue="condition vs property",
                                   reason="node exists; it is stored as both condition and property and must be "
                                          "unified (property, with measurements in observation nodes)"),
    },
    "043": {
        "HfO2": T("correct_concept", "HfO2", actions=["keep"], reason="clean formula node"),
        "ZrO2": T("correct_concept", "ZrO2", actions=["keep"], reason="clean formula node"),
        "SiO2": T("correct_concept", "SiO2", actions=["keep"], reason="clean formula node"),
        "HfO2-ZrO2 superlattice": T("correct_not_normalized", "HfO2-ZrO2 superlattices",
                                    actions=["canonicalize", "type_fix"], type_issue="material/sample",
                                    reason="the superlattice is recorded as material and sample; it is a "
                                           "structure concept that the sample instances realise"),
        "atomic layer deposition": T("correct_not_normalized", "ALD", actions=["alias_split", "canonicalize"],
                                     reason="only the abbreviation is a node; ALD with temperature variants is the "
                                            "same process"),
        "ferroelectric order": T("correct_not_normalized", "mixed ferroelectric-antiferroelectric order",
                                 actions=["split_compound", "alias_split"],
                                 reason="only the mixed FE-AFE compound and phase-specific labels exist; the "
                                        "ferroelectric order concept is missing, and FE must not be promoted to a "
                                        "global alias"),
        "antiferroelectric order": T("correct_not_normalized", "mixed ferroelectric-antiferroelectric order",
                                     actions=["split_compound", "alias_split"],
                                     reason="same compound node as ferroelectric order; AFE must stay paper-scoped"),
        "effective oxide thickness": T("correct_not_normalized", "EOT", actions=["alias_split", "canonicalize"],
                                       reason="symbol-only node; the full name occurs in "
                                              "'leakage-effective oxide thickness (EOT)'"),
    },
    "052": {
        "MXenes": T("correct_concept", "MXenes", actions=["keep", "type_fix"],
                    type_issue="material vs material_class", reason="class node exists with two types"),
        "transition metal carbides": T("correct_not_normalized", "carbides, carbonitrides, and nitrides",
                                       actions=["split_compound"],
                                       reason="carbides and nitrides are merged into one compound node; the paper "
                                              "treats them as a family, so the node should be split and linked"),
        "transition metal nitrides": T("correct_not_normalized", "carbides, carbonitrides, and nitrides",
                                       actions=["split_compound"],
                                       reason="same compound node as the carbides; nitrides need their own concept"),
        "graphene": T("correct_concept", "graphene", actions=["keep"], reason="clean material node"),
        "transition metal dichalcogenides": T("correct_not_normalized",
                                              "transition metal dichalcogenides (TMDCs)",
                                              actions=["alias_split"],
                                              reason="node carries the abbreviation inside the label"),
        "exfoliation": T("correct_not_normalized", "exfoliating the 3D bulk to 2D planer structures",
                         actions=["canonicalize", "split_attribute"],
                         reason="the process is stored as the action sentence; the concept is exfoliation and the "
                                "object ('3D bulk to 2D structures') belongs to the fact"),
        "solid solutions": T("correct_concept", "solid solution", actions=["keep", "type_fix"],
                             type_issue="material_class vs structure",
                             reason="node exists (singular); the structure reading is the one used in the paper"),
        "Mo2TiC2Tx": T("correct_concept", "Mo2TiC2Tx", actions=["keep"], reason="clean formula node"),
    },
    "065": {
        "phosphonic acids": T("correct_concept", "phosphonic acid", actions=["keep"],
                              reason="class node exists (singular); plural is a surface form"),
        "carboxylic acids": T("correct_concept", "carboxylic acid", actions=["keep"],
                              reason="class node exists (singular)"),
        "indium tin oxide": T("correct_not_normalized", "ITO", actions=["alias_split", "canonicalize"],
                              reason="only the abbreviation is a node; the full name is in the evidence and in "
                                     "'indium tin oxide substrate'"),
        "self-assembled monolayer": T("correct_concept", "self-assembled monolayer", actions=["keep", "type_fix"],
                                      type_issue="SAM typed material_class",
                                      reason="structure node exists; SAM is a second node typed material_class and "
                                             "should be its alias"),
        "hole-selective contact": T("correct_concept", "hole-selective contact", actions=["keep"],
                                    reason="component/interface node exists"),
        "perovskite light absorber": T("granularity_different", "perovskite", actions=["add_edge"],
                                       reason="only the material 'perovskite' exists; the functional-layer concept "
                                              "is missing"),
        "one-step solution-coating": T("correct_not_normalized", "one-step solution-coating procedure",
                                       actions=["canonicalize"],
                                       reason="the generic noun 'procedure' is part of the concept name"),
        "wettability": T("confirmed_missing", "", "model_omission", ["targeted_reextract"],
                         reason="the word occurs once, in an extracted chunk that produced triples, but no node "
                                "or field contains it"),
    },
    "095": {
        "Sb2O3": T("correct_concept", "Sb2O3", actions=["keep"], reason="clean formula node"),
        "Sb4O6": T("correct_not_normalized", "Sb4O6 molecules", actions=["canonicalize"],
                   reason="the node includes the instance word 'molecules'; the material is Sb4O6"),
        "MoS2": T("correct_concept", "MoS2", actions=["keep"], reason="clean formula node"),
        "inorganic molecular crystal": T("correct_concept", "inorganic molecular crystal", actions=["keep"],
                                         reason="class node exists"),
        "van der Waals dielectrics": T("correct_not_normalized", "vdW dielectric",
                                       actions=["canonicalize", "type_fix"],
                                       type_issue="material vs material_class",
                                       reason="only the abbreviated form is a node and its type is split; the "
                                              "corpus needs the full name as canonical plus vdW as alias"),
        "standard thermal evaporation deposition": T("correct_not_normalized",
                                                     "standard thermal evaporation deposition (STED)",
                                                     actions=["alias_split"],
                                                     reason="node carries the abbreviation in parentheses"),
        "electron mobility": T("correct_concept", "electron mobility", actions=["keep"],
                               reason="clean property node with observation nodes"),
        "transfer-curve hysteresis": T("correct_not_normalized", "hysteresis reduction",
                                       actions=["canonicalize", "split_attribute"],
                                       reason="only qualified forms (hysteresis reduction, considerable "
                                              "hysteresis, source of hysteresis) exist; the property concept "
                                              "'hysteresis' is missing as a node"),
    },
    "153": {
        "wide-bandgap perovskites": T("correct_not_normalized", "WBG perovskites", actions=["alias_split",
                                                                                            "type_fix"],
                                      type_issue="material vs material_class",
                                      reason="only the abbreviation WBG is a node; the full name is the canonical "
                                             "form and the type must be material_class"),
        "tandem solar cells": T("correct_not_normalized", "TSCs", actions=["alias_split", "canonicalize"],
                                reason="only the abbreviation and qualified variants (perovskite/silicon TSCs) "
                                       "exist"),
        "front absorber": T("confirmed_missing", "", "extracted_not_noded", ["targeted_reextract"],
                            reason="the phrase occurs in evidence ('act as the front absorber') and in "
                                   "'front perovskite absorber' measurement nodes, but there is no component node"),
        "photo-induced phase separation": T("correct_not_normalized", "severe photo-induced phase separation",
                                            actions=["split_attribute", "type_fix"],
                                            type_issue="property vs mechanism",
                                            reason="the severity adjective is inside the name and the type is "
                                                   "wrong for a process phenomenon"),
        "open-circuit voltage deficit": T("correct_not_normalized", "VOC deficit", actions=["canonicalize"],
                                          reason="only abbreviation forms (VOC deficit, V_OC deficit) are nodes"),
        "thermalization losses": T("correct_concept", "thermalization loss", actions=["keep"],
                                   reason="mechanism node exists (singular)"),
        "charge transport layers": T("correct_not_normalized", "charge transport layers and buffer layers",
                                     actions=["split_compound", "type_fix"],
                                     type_issue="typed material",
                                     reason="CTL only exists inside a compound material label; the component concept "
                                            "is missing and CTLs must be an alias"),
        "bandgap complementarity": T("granularity_different", "bandgap", actions=["add_edge"],
                                     reason="only the property 'bandgap' exists; the complementarity concept "
                                            "(the tandem design principle) is missing"),
    },
    "201": {
        "alpha-FAPbI3": T("correct_concept", "α-FAPbI3", actions=["keep"],
                          reason="phase-specific node exists; write it as alpha-FAPbI3 in the canonical layer "
                                 "while keeping the Greek form as a surface form"),
        "delta-FAPbI3": T("correct_concept", "δ-FAPbI3", actions=["keep"],
                          reason="separate phase node exists; it must never merge with the alpha phase"),
        "formamidinium lead triiodide": T("correct_not_normalized", "FAPbI3", actions=["alias_split",
                                                                                       "canonicalize"],
                                          reason="only the formula is a node; the full name and FAPbI3 are "
                                                 "aliases of one material concept covering both phases"),
        "formate": T("correct_concept", "formate", actions=["keep", "alias_split"],
                     reason="formate is a node and HCOO− is a separate node; the ion and the name must become one "
                            "concept with HCOO− as alias"),
        "anion-vacancy defects": T("correct_concept", "anion-vacancy defects", actions=["keep"],
                                   reason="clean defect node"),
        "grain boundaries": T("correct_not_normalized", "defects near the grain boundaries",
                              actions=["split_attribute", "canonicalize"],
                              reason="the structure concept only exists inside a defect phrase; grain boundary "
                                     "is the structure, the defects near it are a separate node"),
        "anion engineering": T("confirmed_missing", "", "preprocess_loss", ["targeted_reextract"],
                               reason="all mentions sit in lines 21-31, which the front-matter stripper removed "
                                      "before extraction (the extraction starts at line ~55)"),
        "crystallinity": T("correct_concept", "crystallinity", actions=["keep"],
                           reason="clean property node"),
    },
    "250": {
        "AgBiS2": T("correct_concept", "AgBiS2", actions=["keep"], reason="clean formula node"),
        "colloidal nanocrystals": T("granularity_different", "AgBiS2 NCs", actions=["add_edge"],
                                    reason="only specific NC labels/instances exist; the class concept "
                                           "('colloidal nanocrystals') is missing"),
        "cation disorder": T("correct_not_normalized", "homogeneous cation disorder",
                             actions=["split_attribute", "type_fix"], type_issue="property vs structure",
                             reason="only the qualified variant is a node and its type is wrong; cation disorder "
                                    "is a structural state"),
        "cation segregation": T("correct_concept", "cation segregation", actions=["keep", "type_fix"],
                                type_issue="property vs structure",
                                reason="node exists; it is a structural state, not a property"),
        "optical transition matrix elements": T("confirmed_missing", "", "preprocess_loss",
                                                ["targeted_reextract"],
                                                reason="the concept only appears in the abstract/intro lines that "
                                                       "were stripped before extraction"),
        "absorption coefficient": T("correct_not_normalized",
                                    "absorption coefficient enhanced by up to a factor of two after annealing",
                                    actions=["split_attribute", "split_compound"],
                                    reason="the property is stored as attribute sentences (enhancement factor, "
                                           "annealing condition, 5-10x comparison); the head concept is missing"),
        "valence band maximum": T("correct_not_normalized", "VBM and CBM delocalized over the entire material",
                                  actions=["split_compound", "alias_split"],
                                  reason="VBM appears only inside a sentence-like compound node; VBM and CBM must be "
                                         "two property concepts with the observation as a fact"),
        "conduction band minimum": T("correct_not_normalized", "VBM and CBM delocalized over the entire material",
                                     actions=["split_compound", "alias_split"],
                                     reason="same compound node as VBM"),
    },
}


# --------------------------------------------------------------------------- #
# Relation adjudications
# --------------------------------------------------------------------------- #
def R(verdict, edges=(), action="keep", reason=""):
    return {"verdict": verdict, "edges": list(edges), "action": action, "reason": reason}


RELATIONS: dict[str, list[dict]] = {
    "001": [
        R("supported", ["4Cl-BZS -> enables -> dual-site Pb2+ passivation"],
          "merge_duplicate", "exact edge exists twice (positions 28 and 34) with the same evidence; merge into "
                             "one relation with a two-entry evidence list"),
        R("supported", ["undercoordinated Pb2+ ions -> exhibits -> nonradiative recombination at the perovskite/CTL interface"],
          "keep", "predicate differs ('exhibits' vs 'results in') but the causal reading is the paper's; the "
                  "object keeps the interface qualifier, which is acceptable"),
        R("supported", ["nonradiative recombination at the perovskite/CTL interface -> limits -> photovoltage and fill factor"],
          "split_object", "the object is a compound (photovoltage and fill factor); the direction and predicate "
                          "are right"),
    ],
    "011": [
        R("supported", ["conductivity modulation effect -> originates from -> hole injection across the PN HJ-interface"],
          "keep", "the reference direction (injection induces modulation) is expressed with the inverse predicate "
                  "on the other side of the same fact; no repair needed"),
        R("not_found", [], "add_edge", "no triple links Ga2O3 to power electronics, although the abstract states "
                                       "the application; the concept-level application edge is missing"),
        R("partially_supported", ["p-NiOx -> used in -> Ga2O3 HJ PN diode"],
          "keep", "the combination is only implied by the device node; no explicit p-NiOx <-> n-Ga2O3 edge"),
    ],
    "021": [
        R("supported", ["quasi-2D perovskite -> exhibits -> quantum-well structures",
                        "quasi-2D perovskite -> exhibits -> natural quantum-well structures",
                        "quasi-2D perovskite -> exhibits -> self-assembled multi-quantum-well structures"],
          "merge_duplicate", "three parallel edges express the same structural fact; merge with an evidence list"),
        R("not_found", [], "add_edge", "the confinement effect is described in the text ('quantum- and "
                                       "dielectric-confinement effects arising from the QW structure') but no edge "
                                       "connects the structure to it"),
        R("partially_supported", ["quasi-2D perovskite -> used in -> solar cells and LEDs"],
          "split_object", "the material's use is expressed, but the object merges solar cells and LEDs, so the "
                          "LED application cannot be retrieved on its own"),
    ],
    "023": [
        R("partially_supported", ["AlGaN ternary alloys -> used in -> UV photodetectors (PDs)",
                                  "AlN/AlGaN SL structures -> used in -> AlGaN solar-blind UV detector"],
          "keep", "the application edge exists but targets the generic 'UV photodetectors (PDs)' node; the "
                  "solar-blind qualifier is not part of the object concept"),
        R("supported", ["AlGaN-based focal plane arrays (FPAs) -> exhibits -> outstanding solar-blind imaging capability"],
          "keep", "same fact with a different predicate; the capability is stated"),
        R("not_found", [], "add_edge", "the 'APD is a photodetector' hierarchy is never emitted; APD is only a "
                                       "device that AlGaN is used in"),
    ],
    "038": [
        R("supported", ["Metal oxide semiconductors -> used in -> commercial gas sensors"], "keep",
          "exact instance of the reference relation"),
        R("not_found", ["noble metal nanoparticles modification -> improves -> response and selectivity"],
          "add_edge", "the modification is described and a process-quality edge exists, but no 'noble metal "
                      "nanoparticles -> modifies -> MOS' edge; the composite mention carries the meaning instead"),
        R("not_found", [], "add_edge", "organic polymers only appear inside the composite label; no modifier edge "
                                       "to MOS exists"),
    ],
    "043": [
        R("not_found", [], "targeted_reextract", "no 'high-k' phrase or dielectric-layer application edge exists "
                                                 "anywhere in the extracted output"),
        R("partially_supported", ["HfO2-ZrO2 -> deposited by -> atomic layer deposition (ALD)"],
          "keep", "the growth method is attached to the stack formula rather than to a 'doped-HfO2' concept"),
        R("supported", ["HfO2-ZrO2 multilayers -> exhibits -> mixed ferroelectric-antiferroelectric order",
                        "mixed FE-AFE order -> improves -> permittivity of the multilayer stack"],
          "merge_duplicate", "the order is attached to the multilayers; the second edge shows the consequence. "
                             "The two should be one relation family (structure -> property) with evidence"),
    ],
    "052": [
        R("supported", ["MXenes -> is a -> 2D material"], "merge_duplicate",
          "exact edge exists three times (positions 0, 196, 328)"),
        R("partially_supported", ["transition metal dichalcogenides (TMDCs) -> synthesized by -> exfoliating the 3D "
                                  "bulk to 2D planer structures"],
          "split_attribute", "predicate and endpoints are semantically right, but the process object is an action "
                             "phrase; the exfoliation concept must be extracted from it"),
        R("supported", ["Mo2TiC2Tx -> has phase -> ordered structure with transition metal atomic sandwiches"],
          "keep", "predicate differs ('has phase' vs 'has structure'); the structural fact is stated"),
    ],
    "065": [
        R("supported", ["phosphonic or carboxylic acids -> self-assemble on -> indium tin oxide substrate"], "keep",
          "exact edge"),
        R("supported", ["self-assembled monolayer -> used in -> hole-selective contact"], "keep",
          "'used in' vs 'used as' is a predicate variant, the role relation is the same"),
        R("not_found", [], "add_edge", "the one-step coating node exists but no edge connects it to the perovskite "
                                       "absorber; evidence for the formation step is in the paragraph"),
    ],
    "095": [
        R("supported", ["Sb2O3 -> deposited by -> standard thermal evaporation deposition (STED)"], "keep",
          "film instance collapsed to the material; predicate 'deposited by' matches the fabrication claim"),
        R("supported", ["Sb2O3 -> composed of -> Sb4O6 molecules"], "keep",
          "the powder instance is collapsed; the composition fact is correct"),
        R("not_found", [], "targeted_reextract", "no 'van der Waals' triple exists at all, although the paper's "
                                                 "central mechanism is vdW bonding of Sb4O6 molecules"),
    ],
    "153": [
        R("partially_supported", ["WBG perovskites -> used in -> tandem architectures"], "add_edge",
          "the evidence sentence says the WBG perovskites 'act as the front absorber', but the relation was "
          "emitted with the tandem architecture as object; the role relation to the front absorber is missing"),
        R("not_found", ["silicon solar cells -> limits -> thermalization loss"], "add_edge",
          "the thermalization-loss concept is used, but the reference claim (front cell reduces it) has no edge"),
        R("supported", ["WBG perovskite solar cells -> exhibits -> severe photo-induced phase separation"], "keep",
          "'has issue' is expressed as 'exhibits severe ...'; the qualifier stays in the object"),
    ],
    "201": [
        R("supported", ["HCOO− -> eliminates -> anion-vacancy defects", "HCOO− -> passivates -> I− vacancy"],
          "merge_duplicate", "the reference relation is expressed through the ion form (alias of formate); the "
                             "two vacancy edges describe the same action on two defect labels"),
        R("partially_supported", ["formate-containing perovskite films -> exhibits -> high crystallinity and large "
                                  "grain size"],
          "split_object", "crystallinity is expressed, but the subject is the treated film and the object merges "
                          "crystallinity with grain size"),
        R("partially_supported", ["FAPbI3 -> has phase -> α-phase", "2% Fo-FAPbI3 film -> exhibits -> absence of δ-phase"],
          "add_edge", "the phase identity and the suppression of the δ phase are captured; the temperature-"
                      "dependent phase transition itself is not"),
    ],
    "250": [
        R("not_found", [], "targeted_reextract", "the abstract/intro lines that state the enhancement were stripped "
                                                 "before extraction; no node or edge survives"),
        R("not_found", [], "targeted_reextract", "no edge connects the nanocrystals to extremely thin absorber "
                                                 "devices; the phrase never appears in the extracted output"),
        R("not_found", [], "targeted_reextract", "the orbital character of the band edges is in the stripped "
                                                 "intro; VBM/CBM only exist as sentence-like compound nodes"),
    ],
}


# --------------------------------------------------------------------------- #
# Confirmed v2 defects found during the review (each needs a repair in Stage B)
# --------------------------------------------------------------------------- #
DEFECTS = [
    {"id": "d-250-direction",
     "kind": "reversed_causal_direction",
     "paper": "250_Wang_2022_Cation-disorder-engineering-yields-AgBiS2-nanocr",
     "edge_position": 157,
     "edge": "absorption coefficients of ternary AgBiS2 NCs -> improves -> cation disorder homogenization under "
             "mild annealing conditions",
     "evidence": "the absorption coefficients of ternary AgBiS2 NCs can be enhanced via cation disorder "
                 "homogenization under mild annealing conditions (raw md line 164)",
     "repair": "rewrite as process -> property: 'cation disorder homogenization under mild annealing conditions "
               "-> improves -> absorption coefficients of ternary AgBiS2 NCs', keep the annealing qualifier",
     "evidence_line": 164},
    {"id": "d-001-duplicate",
     "kind": "duplicate_relation",
     "paper": "001_Chen_2024_Improved-charge-extraction-in-inverted-perovskit",
     "edge_positions": [28, 34],
     "edge": "4Cl-BZS -> enables -> dual-site Pb2+ passivation",
     "repair": "merge into one relation with two evidence records"},
    {"id": "d-052-duplicate",
     "kind": "duplicate_relation",
     "paper": "052_Bhat_2021_Prospects-challenges-and-stability-of-2D-MXenes",
     "edge_positions": [0, 196, 328],
     "edge": "MXenes -> is a -> 2D material",
     "repair": "merge into one relation with three evidence records"},
    {"id": "d-250-longphrase",
     "kind": "attribute_phrase_node",
     "paper": "250_Wang_2022_Cation-disorder-engineering-yields-AgBiS2-nanocr",
     "node": "absorption coefficient enhanced by up to a factor of two after annealing",
     "repair": "concept = absorption coefficient; change/condition/number moved to fact fields"},
    {"id": "d-021-quantum-confinement",
     "kind": "compound_label",
     "paper": "021_Zhang_2021_High-performance-quasi-2D-perovskite-light-emitt",
     "node": "quantum- and dielectric-confinement effects",
     "repair": "split into quantum confinement and dielectric confinement"},
    {"id": "d-043-fe-order",
     "kind": "compound_label",
     "paper": "043_Cheema_2022_Ultrathin-ferroic-HfO2ZrO2-superlattice-gate-sta",
     "node": "mixed ferroelectric-antiferroelectric order",
     "repair": "keep the mixed-order concept and add ferroelectric order / antiferroelectric order as components; "
               "FE and AFE stay paper-scoped aliases"},
    {"id": "d-201-grain-boundaries",
     "kind": "attribute_phrase_node",
     "paper": "201_Jeong_2021_Pseudo-halide-anion-engineering-for-α-FAPbI3-per",
     "node": "defects near the grain boundaries",
     "repair": "grain boundary (structure) + defects (defect) as separate concepts, relation kept as fact"},
    {"id": "d-005-type-conflict",
     "kind": "type_conflict",
     "paper": "multiple",
     "examples": ["perovskite solar cells: device/material_class",
                  "quasi-2D perovskite: material/material_class",
                  "energy transfer: mechanism/process/property",
                  "operating temperature: condition/property",
                  "MXenes: material/material_class"],
     "repair": "concept type resolved by the head-noun rules, conflicts recorded in type_conflicts.json"},
]


def build() -> dict:
    reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
    cases = json.loads((STAGE / "case_files.json").read_text(encoding="utf-8"))
    cases_by_paper = {c["paper"]: c for c in cases}

    term_records, relation_records = [], []
    missing = []
    for ref in reference:
        prefix = ref["paper"][:3]
        term_table = TERMS.get(prefix, {})
        case = cases_by_paper[ref["paper"]]
        case_terms = {t["canonical"]: t for t in case["terms"]}
        for term in ref["terms"]:
            judgement = term_table.get(term["canonical"])
            if judgement is None:
                missing.append((prefix, term["canonical"]))
                continue
            evidence = case_terms.get(term["canonical"], {})
            term_records.append({
                "paper": ref["paper"],
                "paper_kind": ref["kind"],
                "canonical": term["canonical"],
                "category": term["category"],
                "aliases": term.get("aliases") or [],
                "v2_label_status": term.get("v2_status"),
                **judgement,
                "evidence": {
                    "source_mentions": evidence.get("source_mentions"),
                    "source_chunks": evidence.get("source_chunks"),
                    "chunk_triple_counts": evidence.get("chunk_triple_counts"),
                    "body_mentions": (evidence.get("body_mentions") or {}).get("lines"),
                    "body_lines_in_extracted_text": (evidence.get("body_mentions") or {}).get(
                        "lines_in_extracted_text"),
                    "exact_labels": evidence.get("exact_labels"),
                    "near_labels": [n["label"] for n in (evidence.get("near_labels") or [])],
                    "observed_in_fields": evidence.get("observed_in_fields"),
                    "observed_in_evidence_text": evidence.get("observed_in_evidence_text"),
                },
            })
        for index, relation in enumerate(ref["relations"]):
            judgement = RELATIONS[prefix][index]
            candidates = case["relations"][index]["candidates"]
            relation_records.append({
                "paper": ref["paper"],
                "index": index + 1,
                "subject": relation["subject"],
                "predicate": relation["predicate"],
                "object": relation["object"],
                "source_line": relation["line"],
                **judgement,
                "candidate_count": len(candidates),
                "candidates": [f"[{c['position']}] {c['subject']} -> {c['predicate']} -> {c['object']}"
                               for c in candidates][:4],
            })

    if missing:
        raise ValueError(f"terms without adjudication: {missing}")
    if sum(len(v) for v in RELATIONS.values()) != 36:
        raise ValueError("relation adjudication count is not 36")

    term_counts = Counter(record["verdict"] for record in term_records)
    relation_counts = Counter(record["verdict"] for record in relation_records)
    type_conflicts = [record["canonical"] for record in term_records if record.get("type_issue")]
    actions = Counter(action for record in term_records for action in record["actions"])
    metrics = {
        "terms_total": len(term_records),
        "term_verdicts": dict(term_counts),
        "v2_semantic_coverage": round(
            (term_counts["correct_concept"] + term_counts["correct_not_normalized"]) / len(term_records), 4),
        "v2_covered_including_granularity": round(
            (term_counts["correct_concept"] + term_counts["correct_not_normalized"]
             + term_counts["granularity_different"]) / len(term_records), 4),
        "term_type_conflicts": len(type_conflicts),
        "missing_kinds": dict(Counter(record["missing_kind"] for record in term_records if record["missing_kind"])),
        "actions": dict(actions),
        "relations_total": len(relation_records),
        "relation_verdicts": dict(relation_counts),
        "relation_support_rate": round(relation_counts["supported"] / len(relation_records), 4),
        "relation_support_or_partial": round(
            (relation_counts["supported"] + relation_counts["partially_supported"]) / len(relation_records), 4),
    }

    (STAGE / "adjudication_terms.json").write_text(
        json.dumps(term_records, ensure_ascii=False, indent=1), encoding="utf-8")
    (STAGE / "adjudication_relations.json").write_text(
        json.dumps(relation_records, ensure_ascii=False, indent=1), encoding="utf-8")
    (STAGE / "defects.json").write_text(json.dumps(DEFECTS, ensure_ascii=False, indent=1), encoding="utf-8")
    (STAGE / "metrics_reference_set.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=1),
                                                      encoding="utf-8")
    return metrics


if __name__ == "__main__":
    summary = build()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
