# -*- coding: utf-8 -*-
"""Corrected metrics for full_v1 (v2 evaluation).

Fixes the reporting errors of the first assessment:
  * evidence rate is computed on the edges that actually carry the marker
  * predicate counts distinguish all predicate strings / canonical / unmapped
  * type distribution is reported per unique entity, not per edge end
  * duplicates are reported under three groupings with redundant-edge counts
  * failed chunks are reconciled against summary.csv
Output: evaluation/full_v1/metrics_v2.json
"""
import json
import os
import re
from collections import Counter, defaultdict

BASE = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\ai-knowledge-graph-main\evaluation\full_v1\kg_output"
ENR = os.path.join(BASE, "enriched")
OUT = os.path.join(os.path.dirname(BASE), "metrics_v2.json")

triples = []
papers = {}
for f in sorted(os.listdir(ENR)):
    if f.endswith(".json"):
        ts = json.load(open(os.path.join(ENR, f), encoding="utf-8"))
        papers[f[:-5]] = ts
        triples += ts

n = len(triples)
obs = [t for t in triples if str(t.get("object", "")).startswith("obs-")]
ev = [t for t in triples if "evidence_text_match" in t]
ev_ok = sum(1 for t in ev if t.get("evidence_text_match"))
no_src = sum(1 for t in triples if not t.get("source"))

pred_all = Counter(str(t.get("predicate")) for t in triples)
canon = Counter(str(t.get("predicate")) for t in triples if not t.get("unmapped"))
unmapped = Counter(str(t.get("predicate")) for t in triples if t.get("unmapped"))

# type distribution per unique entity (majority vote like the visualiser)
votes = defaultdict(Counter)
for t in triples:
    for name, key in ((t.get("subject"), "subject_type"), (t.get("object"), "object_type")):
        if name and not str(name).startswith("obs-") and t.get(key):
            votes[str(name)][str(t.get(key))] += 1
ent_types = Counter(c.most_common(1)[0][0] for c in votes.values())

# duplicate analysis under three groupings
def dup_stats(keyfn):
    groups = Counter(keyfn(t) for t in obs)
    dups = {k: v for k, v in groups.items() if v > 1}
    involved = sum(dups.values())
    redundant = involved - len(dups)
    return {"groups": len(dups), "edges": involved, "redundant": redundant}

dup_a = dup_stats(lambda t: (str(t.get("subject")).lower(), str(t.get("property")).lower(),
                             str(t.get("value")), str(t.get("unit"))))
dup_b = dup_stats(lambda t: (str(t.get("paper_id")), str(t.get("subject")).lower(),
                             str(t.get("property")).lower(), str(t.get("value")), str(t.get("unit"))))
dup_c = dup_stats(lambda t: (str(t.get("paper_id")), str(t.get("subject")).lower(),
                             str(t.get("property")).lower(), str(t.get("value")), str(t.get("unit")),
                             json.dumps(t.get("conditions"), sort_keys=True, ensure_ascii=False),
                             str(t.get("sample_id")), str(t.get("device_id"))))

GENERIC = {"device", "devices", "control device", "perovskite film", "perovskite films", "film", "films",
           "sample", "samples", "pscs", "perovskite", "material", "materials", "cell", "cells"}
generic_edges = sum(1 for t in triples if str(t.get("subject", "")).strip().lower() in GENERIC)

# failed chunk reconciliation
import csv
summary = list(csv.DictReader(open(os.path.join(BASE, "summary.csv"), encoding="utf-8-sig")))
summary_empty_failed = sum(int(r.get("empty_failed") or 0) for r in summary)
summary_skipped = sum(len([x for x in (r.get("failed_chunk_indices") or "").split(";") if x]) for r in summary)
fc_path = os.path.join(BASE, "failed_chunks.json")
fc = json.load(open(fc_path, encoding="utf-8")) if os.path.exists(fc_path) else {}
fc_empty = sum(len(v.get("empty_failed", [])) for v in fc.values())
fc_skip = sum(len(v.get("skipped", [])) for v in fc.values())

metrics = {
    "papers": len(papers),
    "edges_total": n,
    "observation_edges": len(obs),
    "numeric_edges": sum(1 for t in triples if t.get("value_raw") or re.search(r"\d", str(t.get("object", "")))),
    "evidence": {"marked_edges": len(ev), "matched": ev_ok,
                 "rate_on_marked": round(ev_ok / max(1, len(ev)), 4),
                 "unmarked_edges": n - len(ev),
                 "matched_share_of_all": round(ev_ok / max(1, n), 4),
                 "edges_without_source": no_src},
    "predicates": {"all_strings": len(pred_all), "canonical_strings": len(canon),
                   "unmapped_strings": len(unmapped), "unmapped_edges": sum(unmapped.values()),
                   "canonical_edges": sum(canon.values())},
    "entity_types_unique": dict(ent_types.most_common()),
    "duplicates": {"subject_property_value_unit": dup_a,
                   "plus_paper_scope": dup_b,
                   "plus_conditions_and_ids": dup_c},
    "generic_hub_edges": generic_edges,
    "long_objects": sum(1 for t in triples if len(str(t.get("object"))) > 120),
    "failed_chunks": {"summary_empty_failed": summary_empty_failed,
                      "summary_skipped": summary_skipped,
                      "log_empty_failed": fc_empty, "log_skipped": fc_skip,
                      "log_total": fc_empty + fc_skip},
}

json.dump(metrics, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k, v in metrics.items():
    print(f"{k}: {v}")
print("\nwritten", OUT)
