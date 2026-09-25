# -*- coding: utf-8 -*-
"""
Compute agreement between independent human recoding and frozen AI-assisted labels.

REFUSES TO RUN unless the judgement columns are actually filled. This guard is
deliberate: it prevents an empty sheet from being turned into a result.

Usage:  python compute_agreement_v8.py
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
V7 = Path(r"C:/Users/fengq/Desktop/AI健康医学_Applied_Sciences_v7_20260920_175106/02_supplement")

SHEET = HERE / "blinded_coding_sheet_v8.csv"
KEY = HERE / "sealed_key_v8.csv"

VALID = {"supported", "not_recovered", "unclear", "not_applicable"}


def fail(msg: str) -> None:
    print("REFUSED:", msg)
    print("This script computes results only from real completed human coding.")
    sys.exit(1)


def main() -> None:
    rows = list(csv.DictReader(open(SHEET, encoding="utf-8-sig")))
    filled1 = [r for r in rows if (r.get("coder1_status") or "").strip()]
    if len(filled1) < len(rows):
        fail(f"coder1_status filled for {len(filled1)}/{len(rows)} items.")
    bad = [r["item_id"] for r in rows if r["coder1_status"].strip() not in VALID]
    if bad:
        fail(f"{len(bad)} items have an out-of-vocabulary status, e.g. {bad[:5]}")

    # unmask and join to frozen AI-assisted labels
    key = {r["item_id"]: (r["record_id_real"], r["field"], r["component"])
           for r in csv.DictReader(open(KEY, encoding="utf-8-sig"))}
    ai = {}
    for d in csv.DictReader(open(V7 / "component_decisions_v7_1400.csv", encoding="utf-8-sig")):
        ai[(d["record_id"], d["field"], d["component"])] = (
            "supported" if d.get("v6_primary_support_status") == "supported_by_retained_evidence"
            else "not_recovered")

    a = b = c = d = 0
    human_supported = 0
    for r in rows:
        rec, fld, comp = key[r["item_id"]]
        ai_state = ai.get((rec, fld, comp))
        h = r["coder1_status"].strip()
        if ai_state is None:
            fail(f"no frozen label found for {r['item_id']}")
        hp, ap = h == "supported", ai_state == "supported"
        if hp:
            human_supported += 1
        if hp and ap:
            a += 1
        elif hp and not ap:
            b += 1
        elif not hp and ap:
            c += 1
        else:
            d += 1

    n = len(rows)
    po = (a + d) / n
    pe = ((a + b) / n) * ((a + c) / n) + ((c + d) / n) * ((b + d) / n)
    kappa = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    # Gwet's AC1
    pi = (((a + b) / n) + ((a + c) / n)) / 2
    ac1 = (po - pi) / (1 - pi) if pi < 1 else float("nan")

    out = {
        "n": n,
        "cross_tabulation": {"human_supported_ai_supported": a,
                             "human_supported_ai_not_recovered": b,
                             "human_not_recovered_ai_supported": c,
                             "human_not_recovered_ai_not_recovered": d},
        "human_supported_total": human_supported,
        "ai_supported_total": a + c,
        "raw_agreement": round(po, 4),
        "cohens_kappa": round(kappa, 4),
        "gwets_ac1": round(ac1, 4),
    }
    print(json.dumps(out, indent=1))
    (HERE / "agreement_result_v8.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
