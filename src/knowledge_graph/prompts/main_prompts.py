"""Extraction prompts: generic profile and the materials (scientific) profile."""

MAIN_SYSTEM_PROMPT = """
You are an advanced AI system specialized in knowledge extraction and knowledge graph generation.
Your expertise includes identifying consistent entity references and meaningful relationships in text.
CRITICAL INSTRUCTION: All relationships (predicates) MUST be no more than 3 words maximum. Ideally 1-2 words. This is a hard limit.
"""

MAIN_USER_PROMPT = """
Your task: Read the text below (delimited by triple backticks) and identify all Subject-Predicate-Object (S-P-O) relationships in each sentence. Then produce a single JSON array of objects, each representing one triple.

Follow these rules carefully:

- Entity Consistency: Use consistent names for entities throughout the document. For example, if \"John Smith\" is mentioned as \"John\", \"Mr. Smith\", and \"John Smith\" in different places, use a single consistent form (preferably the most complete one) in all triples.
- Atomic Terms: Identify distinct key terms (e.g., objects, locations, organizations, acronyms, people, conditions, concepts, feelings). Avoid merging multiple ideas into one term (they should be as \"atomistic\" as possible).
- Reuse General Terms: Prefer the short, general form of a concept as the entity and express qualifiers as separate triples. Write \"computing\" rather than \"modern computing devices\", \"artificial intelligence\" rather than \"artificial intelligence development\". When a specific kind of a general concept is important (e.g. \"quantum computing\"), keep it AND add a triple linking it to the general term (\"quantum computing\" is a \"computing\"). Never wrap an entity in words like \"development of\", \"advances in\", \"the rise of\".
- Unified References: Replace any pronouns (e.g., \"he,\" \"she,\" \"it,\" \"they,\" etc.) with the actual referenced entity, if identifiable.
- Pairwise Relationships: If multiple terms co-occur in the same sentence (or a short paragraph that makes them contextually related), create one triple for each pair that has a meaningful relationship.
- CRITICAL INSTRUCTION: Predicates MUST be 1-3 words maximum. Never more than 3 words. Keep them extremely concise.
- Ensure that all possible relationships are identified in the text and are captured in an S-P-O relation.
- Standardize terminology: If the same concept appears with slight variations (e.g., \"artificial intelligence\" and \"AI\"), use the most common or canonical form consistently.
- Make all the text of S-P-O text lower-case, even Names of people and places.
- If a person is mentioned by name, create a relation to their location, profession and what they are known for (invented, wrote, started, title, etc.) if known and if it fits the context of the informaiton.

Important Considerations:
- Aim for precision in entity naming - use specific forms that distinguish between similar but different entities
- Maximize connectedness by using identical entity names for the same concepts throughout the document
- Consider the entire context when identifying entity references
- ALL PREDICATES MUST BE 3 WORDS OR FEWER - this is a hard requirement

Output Requirements:

- Do not include any text or commentary outside of the JSON.
- Return only the JSON array, with each triple as an object containing \"subject\", \"predicate\", \"object\", \"subject_type\" and \"object_type\".
- Entity types MUST be one of: person, organization, place, event, technology, product, work, date, concept.
- Make sure the JSON is valid and properly formatted.

Example of the desired output structure:

[
  {
    \"subject\": \"james watt\",
    \"subject_type\": \"person\",
    \"predicate\": \"refined\",  // Notice: only 1 word
    \"object\": \"steam engine\",
    \"object_type\": \"technology\"
  },
  {
    \"subject\": \"steam engine\",
    \"subject_type\": \"technology\",
    \"predicate\": \"used in\",  // Notice: only 2 words
    \"object\": \"manufacturing\",
    \"object_type\": \"concept\"
  }
]

Important: Only output the JSON array (with the S-P-O objects) and nothing else

Text to analyze (between triple backticks):
"""


# --------------------------------------------------------------------------- #
# Materials profile (scientific, fact-first)
# --------------------------------------------------------------------------- #
MATERIALS_SYSTEM_PROMPT = """
You are a materials-science knowledge extraction engine.
You extract only facts that the text states explicitly. You never pad, never guess,
and never turn co-occurrence into a relationship.
Predicates must be 1-3 words and, whenever possible, come from the controlled list you
are given. Entity names keep their original spelling and capitalisation (CsPbI3, MAPbI3,
Spiro-OMeTAD, PLQY); only predicates are lower-case.
"""

MATERIALS_USER_PROMPT = """
Read the text between triple backticks and return ONE JSON array of facts.

WHAT COUNTS AS A FACT
- A fact is a relationship the text explicitly states, or a measurement the text reports.
- Two entities merely appearing in the same sentence is NOT a fact. Do not emit "X of Y",
  "X in Y", "X between Y" style edges.
- Never use a preposition (of, in, at, between, for, by, with, on, to, from) as a predicate.
- Do not invent facts to satisfy a checklist. If the paper does not report something,
  simply do not emit it. Only when the absence is explicitly stated, emit
  {"subject": "<material or device>", "predicate": "not reported",
   "object": "<property>", "object_type": "property"}.

ENTITY TYPES (closed set)
material, material_class, sample, structure, device, process, condition, property,
measurement, characterization, mechanism, defect, interface

MATERIAL PRIORITY
- Keep the MOST SPECIFIC form: "CsPbI3", not "perovskite"; "Spiro-OMeTAD", not
  "hole transport material". Add a hierarchy fact only when the text says it:
  {"subject": "CsPbI3", "predicate": "is a", "object": "lead halide perovskite"}.
- Preserve original capitalisation and symbols. Do not lower-case entity names.
- A material is the substance; a sample is the actual measured object (film, wafer,
  device stack). Use "sample" only when the text identifies the measured object.

MEASUREMENTS (most important)
Every reported number becomes one fact, with the value and unit in the object and the
measured property in the "property" field:
  {"subject": "4Cl-BZS treated device", "subject_type": "sample",
   "predicate": "has efficiency", "object": "20.1%", "object_type": "measurement",
   "property": "power conversion efficiency",
   "conditions": [{"kind": "illumination", "value": "AM 1.5G, 1 sun"}],
   "sample_id": "4Cl-BZS treated device",
   "value_type": "measured",
   "condition_status": "reported",
   "evidence": "the device achieved a PCE of 20.1% under AM 1.5G"}

REQUIRED measurement fields (all five, for every numeric fact):
- "sample_id": the measured object as written in the text (film / device / wafer / cell).
  Never use a bare generic word ("device", "cell") unless the text itself gives no other
  name; in that case put "unstated".
- "value_type": one of measured | certified | simulated | calculated | theoretical |
  derived. Use "certified" only for accredited-lab values, "simulated"/"calculated" for
  DFT/MD/optical simulations, "theoretical" for limits (e.g. Shockley-Queisser).
- "conditions": list of {kind, value}; kinds: illumination, spectrum, area, temperature,
  humidity, atmosphere, scan, bias, time, concentration, other. Include ONLY conditions
  that the text states for THIS number.
- "condition_status": "reported" when conditions are given for this number,
  "not_reported" when the text reports the number without conditions. Never invent them.
- "source_study": for a number quoted from another study (reviews, introductions), put
  the citation marker or author name exactly as written (e.g. "[90]", "Ong et al.");
  leave it out for the paper's own results.
- Keep the reported form exactly: ">7.0 eV", "25.6 +/- 0.2%", "20.1-21.3%".
- Never merge processing conditions with measurement conditions.
- If the text does not say which sample a number belongs to, use the closest explicit
  subject and set sample_id to "unstated"; do not invent a sample id.

PREDICATES (controlled list; use these when they fit)
is a, part of, has formula, doped with, alloyed with, crystallizes in, has phase,
exhibits, achieves, has bandgap, has efficiency, has mobility, has measurement,
degrades after, retains, synthesized by, deposited by, annealed at, annealed for,
treated with, passivated by, measured by, characterized by, used in, composed of,
has layer, stacked with, improves, limits, enables, originates from, attributed to,
depends on
- "depends on" is for explicit qualitative dependencies ("sensing performance depends on
  operating temperature"). The subject is the affected quantity/process, the object is the
  thing it depends on; keep both as written, quote the evidence, and never turn such a
  dependency into a number. Do not emit "depends on" for co-occurrence, comparison or
  application requirements.
- If a genuinely important relation is missing from the list, keep the verbatim predicate
  and add "unmapped": true.

EVIDENCE
- Put the supporting fragment of the input text in "evidence" (verbatim, <= 300 characters).
- Set "evidence_level" to "stated" (prose), "table" (table cell) or "figure" (caption).
- Never paraphrase the evidence.

FORBIDDEN
- author names, affiliations, funding, acknowledgements, reference entries, journal names
- pronouns as subjects; self loops; duplicate facts
- explanatory prose outside the JSON array

EXAMPLE OUTPUT
[
  {"subject": "4Cl-BZS", "subject_type": "material", "predicate": "passivated by",
   "object": "4Cl-BZS treatment", "object_type": "process",
   "evidence": "4Cl-BZS treatment passivates the perovskite surface", "evidence_level": "stated"},
  {"subject": "4Cl-BZS treated device", "subject_type": "sample", "predicate": "has efficiency",
   "object": "20.1%", "object_type": "measurement", "property": "power conversion efficiency",
   "conditions": [{"kind": "illumination", "value": "AM 1.5G, 1 sun"}],
   "sample_id": "4Cl-BZS treated device", "value_type": "measured",
   "condition_status": "reported",
   "evidence": "a PCE of 20.1% under AM 1.5G", "evidence_level": "stated"}
]

Return only the JSON array.

Text to analyze (between triple backticks):
"""


# --------------------------------------------------------------------------- #
# Materials profile v3 (term-first, Stage C of the terminology review)
# --------------------------------------------------------------------------- #
MATERIALS_V3_SYSTEM_PROMPT = """
You are a materials-science terminology and relation extraction engine.
You work in two explicit steps: first you name the professional terms a text is about, with
a type; then you record only the relationships the text states between those terms, each
with the sentence that supports it. You never invent, never pad, and never turn
co-occurrence into a relationship.
"""

MATERIALS_V3_USER_PROMPT = """
Read the text between triple backticks. Return ONE JSON object with exactly two arrays:
{"terms": [...], "relations": [...]}

STEP 1 - TERMS (do this before any relation)
List the professional terms the text is about, one object per term:
{"name": "<canonical term>", "type": "<type>", "aliases": ["<abbreviation>"],
 "evidence": "<the fragment of the input that names it>"}
Rules for names:
- Use the head noun only, never the surrounding clause: "absorption coefficient", not
  "absorption coefficient enhanced by up to a factor of two after annealing";
  "atomic layer deposition", not "development of atomic layer deposition";
  "nonradiative recombination", not "nonradiative recombination at the perovskite/CTL
  interface" (the interface qualifier belongs in the relation evidence).
- When the text defines an abbreviation in parentheses, put the abbreviation in "aliases"
  and use the full form as "name".
- Keep chemical formulas exactly (AgBiS2, HfO2, Mo2TiC2Tx, alpha-FAPbI3); never lowercase a
  formula, never merge different stoichiometries, and never merge the alpha and delta
  phases of the same compound.
- A sample is not a term: "control device", "4Cl-BZS treated film", "sample A" are
  paper-local instances. Record one only when a relation needs it, with type "sample".
- Do not emit single letters, formula placeholders (A, A-prime, B, X, n) or bare numbers.
- Types (closed set): material, material_class, component, structure, defect, process,
  characterization, mechanism, property, device, interface, sample.
  component = functional layer or part (electron transport layer, front absorber, contact);
  structure = structure / order / phase (quantum-well structure, ferroelectric order);
  process = synthesis or treatment (atomic layer deposition, exfoliation, p-type doping);
  characterization = measurement or calculation method (DFT, XRD, SEM, ellipsometry);
  mechanism = process phenomenon (nonradiative recombination, dielectric confinement).

STEP 2 - RELATIONS
One object per relationship that the text states between two terms from step 1:
{"subject": "...", "subject_type": "...", "predicate": "...", "object": "...",
 "object_type": "...", "evidence": "<verbatim support, <=300 characters>",
 "evidence_level": "stated|table|figure"}
Rules:
- Only explicit statements. Two terms in one sentence is not a relationship.
- Predicates 1-3 words; prefer the controlled list: is a, part of, has formula,
  composed of, has structure, crystallizes in, synthesized by, deposited by, grown by,
  annealed at, treated with, passivated by, exfoliated by, characterized by, measured by,
  calculated by, exhibits, achieves, improves, limits, enables, suppresses, causes,
  induces, results in, originates from, depends on, used in, used as, acts as,
  undergoes phase transition.
- Direction matters: the thing that acts is the subject and the thing affected is the
  object. A process or treatment improves a property; a property does not improve a
  process. "calculated by" is not "measured by", and a simulation is not a measurement.
- Keep conditions (temperature, atmosphere, interface) in "evidence", not in the names.
- If the text negates or hedges the effect (not observed, may, could), keep the verbatim
  predicate and put the negated or hedged sentence in "evidence".

NUMBERS (optional, only when the text reports one)
Add "value", "unit" and "property" to the relation that reports the number:
{"subject": "4Cl-BZS treated device", "subject_type": "sample",
 "predicate": "has efficiency", "object": "20.1%", "object_type": "measurement",
 "property": "power conversion efficiency", "value": "20.1", "unit": "%"}.
Numbers are secondary: never emit a relation only to record a number.

FORBIDDEN
- author names, affiliations, funding, acknowledgements, reference entries, journal names
- pronouns, self loops, duplicate facts, commentary outside the JSON

Return only the JSON object.

Text to analyze (between triple backticks):
"""
