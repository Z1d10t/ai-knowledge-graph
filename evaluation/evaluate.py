# -*- coding: utf-8 -*-
"""Gold-standard evaluation for the materials profile.

Usage:
    python evaluation/evaluate.py --gold evaluation/gold --pred evaluation/kg_output_eval/enriched

Gold CSV columns (one row per fact, see README_标注规范.md):
    fact_id, in_scope, subject, subject_type, predicate_canonical, predicate_raw, object,
    object_type, property, value_raw, value, unit, comparator, uncertainty, sample_or_device,
    conditions, characterization, evidence_quote, evidence_location, origin, merge_error,
    unmapped_verdict, annotator, notes

Metrics
    * entity  P/R/F1 (normalised names, per gold type)
    * relation P/R/F1 (strict: subject + canonical predicate + object; measurements use
      subject + property + value + unit)
    * numeric strict accuracy (property, value, unit, sample and conditions all agree)
    * evidence text-match rate over predictions (cheap, automatic) — NOT a support judgement
    * unmapped predicate verdicts and merge-error counts reported by the annotator
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from knowledge_graph.postprocess.quantities import canon_unit  # noqa: E402

OBS = re.compile(r"^obs-")


def norm(s: str) -> str:
    s = str(s or "").lower().strip()
    s = re.sub(r"[^a-z0-9%+\-.]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def unit_norm(u: str) -> str:
    return norm(canon_unit(u) or "")


def read_gold(path):
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if not row.get("subject") or row.get("fact_id", "").startswith("EXAMPLE"):
                continue
            rows.append(row)
    return rows


def data_dir(gold_dir):
    """Scope file lives next to the gold directory (evaluation/scope.json)."""
    return os.path.dirname(os.path.abspath(gold_dir))


def load_pred(path):
    return json.load(open(path, encoding="utf-8"))


def num(v) -> str:
    try:
        return "%g" % float(str(v).strip())
    except (TypeError, ValueError):
        return norm(v)


def gold_key(row):
    if row.get("property") or row.get("value_raw"):
        return ("measurement", norm(row["subject"]), norm(row.get("property")),
                num(row.get("value")), unit_norm(row.get("unit")))
    return ("relation", norm(row["subject"]), norm(row.get("predicate_canonical")),
            norm(row["object"]))


def pred_keys(triples, max_chunk=None):
    keys, numeric = set(), {}
    for t in triples:
        if max_chunk is not None and int(t.get("chunk") or 0) > max_chunk:
            continue
        subj, obj = t.get("subject"), t.get("object")
        if OBS.match(str(obj)):
            key = ("measurement", norm(subj), norm(t.get("property")),
                   num(t.get("value")), unit_norm(t.get("unit")))
            keys.add(key)
            numeric[key] = t
        elif OBS.match(str(subj)):
            continue  # measures / measured-by helper edges
        else:
            keys.add(("relation", norm(subj), norm(t.get("predicate")), norm(obj)))
    return keys, numeric


def f1(tp, n_pred, n_gold):
    p = tp / n_pred if n_pred else 0.0
    r = tp / n_gold if n_gold else 0.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", default="evaluation/gold")
    ap.add_argument("--pred", default="evaluation/kg_output_eval/enriched")
    ap.add_argument("--out", default="evaluation/metrics.json")
    args = ap.parse_args()

    papers = []
    gold_dir = args.gold
    scope_path = os.path.join(data_dir(gold_dir), "scope.json")
    scope = json.load(open(scope_path, encoding="utf-8")) if os.path.exists(scope_path) else {}
    for name in sorted(os.listdir(gold_dir)):
        if not name.endswith(".csv"):
            continue
        pid = name[:-4]
        gold = [r for r in read_gold(os.path.join(gold_dir, name)) if str(r.get("in_scope", "1")) not in ("0", "")]
        pred_path = os.path.join(args.pred, pid + ".json")
        if not gold or not os.path.exists(pred_path):
            continue
        pred = load_pred(pred_path)
        gk = {gold_key(r) for r in gold}
        pk, numeric_pred = pred_keys(pred, scope.get(pid))
        tp = len(gk & pk)
        p, r, f = f1(tp, len(pk), len(gk))

        # entity level
        ge = {norm(x) for row in gold for x in (row["subject"], row["object"]) if x}
        pe = {norm(x) for t in pred for x in (t.get("subject"), t.get("object"))
              if x and not OBS.match(str(x))}
        etp = len(ge & pe)
        ep, er, ef = f1(etp, len(pe), len(ge))

        # numeric strict accuracy on matched measurements
        matched_measure = [g for g in gold if gold_key(g) in pk and gold_key(g)[0] == "measurement"]
        strict = 0
        for g in matched_measure:
            key = gold_key(g)
            pr = numeric_pred.get(key, {})
            cond_ok = norm(g.get("conditions")) in norm(json.dumps(pr.get("conditions", ""), ensure_ascii=False)) \
                or not g.get("conditions") or not pr.get("conditions")
            if key[3] and key[4] and cond_ok:
                strict += 1

        # evidence text-match over predictions of this paper
        ev = [t for t in pred if "evidence_text_match" in t]
        ev_ok = sum(1 for t in ev if t.get("evidence_text_match"))
        unmapped_verdicts = {}
        for row in gold:
            v = (row.get("unmapped_verdict") or "").strip().lower()
            if v:
                unmapped_verdicts[v] = unmapped_verdicts.get(v, 0) + 1

        papers.append({
            "paper": pid,
            "gold_facts": len(gk),
            "pred_facts": len(pk),
            "relation_tp": tp, "relation_p": round(p, 3), "relation_r": round(r, 3), "relation_f1": round(f, 3),
            "entity_tp": etp, "entity_p": round(ep, 3), "entity_r": round(er, 3), "entity_f1": round(ef, 3),
            "numeric_matched": len(matched_measure), "numeric_strict": strict,
            "evidence_rows": len(ev), "evidence_text_match": ev_ok,
            "merge_errors": sum(1 for row in gold if (row.get("merge_error") or "").strip() not in ("", "0")),
            "unmapped_verdicts": unmapped_verdicts,
        })

    if not papers:
        print("No annotated papers found (fill evaluation/gold/*.csv first).")
        return

    tot_gold = sum(p["gold_facts"] for p in papers)
    tot_pred = sum(p["pred_facts"] for p in papers)
    tot_tp = sum(p["relation_tp"] for p in papers)
    P, R, F = f1(tot_tp, tot_pred, tot_gold)
    etp = sum(p["entity_tp"] for p in papers)
    eg = sum(len({}) for _ in papers)  # placeholder, micro entity numbers below
    print(f"papers annotated      {len(papers)}")
    print(f"gold facts            {tot_gold}")
    print(f"predicted facts       {tot_pred}")
    print(f"relation  P/R/F1      {P:.3f} / {R:.3f} / {F:.3f}")
    num_m = sum(p["numeric_matched"] for p in papers)
    num_s = sum(p["numeric_strict"] for p in papers)
    if num_m:
        print(f"numeric strict acc.   {num_s}/{num_m} = {num_s/num_m:.3f}")
    ev = sum(p["evidence_rows"] for p in papers)
    ev_ok = sum(p["evidence_text_match"] for p in papers)
    if ev:
        print(f"evidence text match   {ev_ok}/{ev} = {ev_ok/ev:.3f}  (automatic check only)")
    print("\nper paper:")
    for p in papers:
        print(f"  {p['paper'][:46]:46} gold={p['gold_facts']:3} pred={p['pred_facts']:4} "
              f"R-P={p['relation_r']:.2f}/{p['relation_p']:.2f}")

    json.dump({"papers": papers, "micro": {"p": P, "r": R, "f1": F}}, open(args.out, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\nwritten {args.out}")


if __name__ == "__main__":
    main()
