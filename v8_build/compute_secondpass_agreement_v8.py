# -*- coding: utf-8 -*-
"""Unseal the key and compute agreement between the original labels and the agent's
blinded second-pass recoding of the 120-item simple random sample."""
from __future__ import annotations
import csv, json
from collections import Counter, OrderedDict
from pathlib import Path
csv.field_size_limit(10**9)
ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "02_supplement" / "blinded_review_package_v8"

key = {r["item_id"]: r for r in csv.DictReader(open(PKG/"sealed_key_v8.csv", encoding="utf-8-sig"))}
# The sealed key carries only the record mapping; the original label is looked up from the
# frozen decision table by (record_id, field, component).
_dec = {(d["record_id"], d["field"], d["component"]): d["component_status"]
        for d in csv.DictReader(open(ROOT/"02_supplement"/"component_decisions_v7_1400.csv", encoding="utf-8-sig"))}
def original_status(item: dict) -> str:
    return _dec.get((item["record_id_real"], item["field"], item["component"]), "")
agent = {r["item_id"]: r for r in csv.DictReader(
    open(r"C:/Users/fengq/WorkBuddy/2026-09-06-21-48-32/blind_coding_agent_v8.csv", encoding="utf-8-sig"))}
print("key items:", len(key), "| agent items:", len(agent))

common = [i for i in agent if i in key]
print("matched:", len(common))

def binarise(s: str) -> str:
    s = (s or "").strip().lower()
    return "supported" if s == "supported" else "not_recovered"

cm = Counter()
disagree = []
for i in common:
    o = binarise(original_status(key[i]))
    a = binarise(agent[i]["agent_status"])
    cm[(o, a)] += 1
    if o != a:
        disagree.append(OrderedDict([
            ("item_id", i),
            ("field", key[i].get("field", "")),
            ("component", key[i].get("component", "")),
            ("original", o), ("second_pass", a),
            ("direction", "second_pass_adds_support" if a == "supported" else "original_supported_second_pass_not"),
            ("note", agent[i]["agent_note"]),
        ]))

n = len(common)
agree = cm[("supported","supported")] + cm[("not_recovered","not_recovered")]
po = agree / n
pe = ((cm[("supported","supported")] + cm[("supported","not_recovered")]) / n) * \
     ((cm[("supported","supported")] + cm[("not_recovered","supported")]) / n) + \
     ((cm[("not_recovered","not_recovered")] + cm[("not_recovered","supported")]) / n) * \
     ((cm[("not_recovered","not_recovered")] + cm[("supported","not_recovered")]) / n)
kappa = (po - pe) / (1 - pe) if pe < 1 else float("nan")

print()
print(f"n = {n}")
print(f"observed agreement = {agree}/{n} = {po*100:.1f}%")
print(f"Cohen's kappa = {kappa:.3f}")
print()
print("confusion matrix (rows = original, cols = second pass)")
print(f"{'':16s} {'supported':>10s} {'not_recov':>10s}")
for o in ("supported","not_recovered"):
    print(f"{o:16s} {cm[(o,'supported')]:10d} {cm[(o,'not_recovered')]:10d}")
print()
print("disagreements:", len(disagree))
print("  second pass adds support:", sum(1 for d in disagree if d['direction']=='second_pass_adds_support'))
print("  second pass removes support:", sum(1 for d in disagree if d['direction']!='second_pass_adds_support'))
print()
print("disagreements by component:")
for k, v in Counter((d["field"]+"/"+d["component"]) for d in disagree).most_common():
    print(f"   {k:42s} {v}")

out = OrderedDict([
    ("release", "v8 second-pass audit"),
    ("design", "simple random sample of 120 of 1,400 decisions, seed 20260924; no stratification"),
    ("blinding", "original labels sealed during coding; unsealed only after all 120 were coded"),
    ("caveat", "Second pass performed by the same class of agent that produced the original labels. "
               "Blinding here is information isolation, not rater independence. The statistics below "
               "are NOT inter-rater reliability estimates and must not be reported as human validation."),
    ("n", n),
    ("observed_agreement", round(po, 4)),
    ("cohen_kappa", round(kappa, 4)),
    ("confusion_matrix", {f"{o}->{a}": cm[(o, a)] for o in ("supported","not_recovered")
                          for a in ("supported","not_recovered")}),
    ("disagreements", disagree),
])
json.dump(out, open(ROOT/"02_supplement"/"second_pass_agreement_v8.json", "w", encoding="utf8"),
          indent=1, ensure_ascii=False)
csv.DictWriter(open(ROOT/"02_supplement"/"second_pass_disagreements_v8.csv", "w", newline="", encoding="utf-8-sig"),
               fieldnames=list(disagree[0].keys()) if disagree else ["item_id"]).writeheader()
if disagree:
    csv.DictWriter(open(ROOT/"02_supplement"/"second_pass_disagreements_v8.csv", "a", newline="", encoding="utf-8-sig"),
                   fieldnames=list(disagree[0].keys())).writerows(disagree)
print("\nwritten second_pass_agreement_v8.json / second_pass_disagreements_v8.csv")
