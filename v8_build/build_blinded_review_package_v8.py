# -*- coding: utf-8 -*-
"""
Build the independent-human-review package (v8).

Reviewer point 3: the primary result has no independent human recoding. Author
confirmation of changed and low-confidence decisions cannot find errors that
were never flagged as uncertain, including false negatives.

This script PREPARES the review. It does NOT perform it and does NOT fabricate
any review record. Every judgement column is written empty.

What it produces (02_supplement/blinded_review_package_v8/):

  README_blinded_review_protocol_v8.md  - protocol, rules, what must not be done
  blinded_coding_sheet_v8.csv           - 1,400 decisions, randomised order,
                                          masked IDs, retained text included,
                                          NO AI label and NO AI rationale
  component_definitions_v8.csv          - the 14 frozen component definitions
  adjudication_log_template_v8.csv      - disagreement and adjudication record
  cross_tabulation_template_v8.md       - the table to fill once coding returns
  sealed_key_v8.csv                     - masked ID -> real record/component
                                          (kept sealed until coding is returned)
  compute_agreement_v8.py               - runs ONLY on a filled sheet; refuses
                                          to run on an empty one

Randomisation uses a fixed seed so the sheet is reproducible.
"""
from __future__ import annotations

import csv
import json
import random
from collections import OrderedDict
from pathlib import Path

csv.field_size_limit(10 ** 9)

FROZEN_LOCAL = Path(__file__).resolve().parent.parent / "02_supplement"
FROZEN_V7 = Path(r"C:/Users/fengq/Desktop/AI健康医学_Applied_Sciences_v7_20260920_175106/02_supplement")
# Prefer the copies bundled with this release so v8 is self-contained;
# fall back to the original v7 location if they are absent.
V7 = FROZEN_LOCAL if (FROZEN_LOCAL / "source_registry.csv").exists() else FROZEN_V7
OUT = Path(__file__).resolve().parent.parent / "02_supplement" / "blinded_review_package_v8"
OUT.mkdir(parents=True, exist_ok=True)

SEED = 20260924
MAX_TEXT = 2400  # characters of retained text shown per decision

COMPONENT_DEFINITIONS = OrderedDict([
    (("exposure", "unit"), "the unit whose exposure opportunity is described"),
    (("exposure", "eligibility"), "the rule defining entry to the opportunity set"),
    (("exposure", "time_origin"), "the anchor from which exposure opportunity is counted"),
    (("exposure", "coverage"), "the extent of the eligible set that is represented"),
    (("follow_up", "calendar_interval"), "a bounded later-observation interval"),
    (("follow_up", "exposure_qualified_observation"),
     "a later observation tied to qualified exposure"),
    (("follow_up", "trace_coverage"), "coverage of logs or observation channels"),
    (("follow_up", "owner"), "the responsible monitoring or disposition role"),
    (("closure", "scope"), "the matter covered by the final disposition"),
    (("closure", "evidence_basis"), "the evidence supporting the final disposition"),
    (("closure", "date"), "the effective disposition date"),
    (("closure", "owner"), "the responsible monitoring or disposition role"),
    (("closure", "uncertainty"), "unresolved matters retained at disposition"),
    (("closure", "reopening_rule"), "the trigger or procedure for reopening"),
])

EXCLUSION_RULE = (
    "Do not count: page navigation; advertisements; recommended or related links; "
    "headers and footers; unrelated sidebars; generic framework or policy text; "
    "taxonomy or classification tag blocks; the same words used in a sense unrelated "
    "to the target event; headlines of external articles where only the headline and "
    "not the article content is retained."
)

STATES = "supported | not_recovered | unclear | not_applicable"


def retained_text(registry_row: dict) -> str:
    parts = []
    for col in ("source_excerpt", "evidence_excerpt_v25", "reverification_excerpt",
                "v29_exposure_denominator_present_evidence_excerpt",
                "v29_follow_up_window_present_evidence_excerpt",
                "v29_closure_basis_present_evidence_excerpt"):
        t = (registry_row.get(col) or "").strip()
        if t:
            parts.append(f"[{col}]\n{t}")
    joined = "\n\n".join(parts)
    if len(joined) > MAX_TEXT:
        joined = joined[:MAX_TEXT] + "\n... [truncated for review sheet]"
    return joined


def main() -> None:
    registry = {r["record_id"]: r for r in
                csv.DictReader(open(V7 / "source_registry.csv", encoding="utf-8-sig"))}
    decisions = list(csv.DictReader(open(V7 / "component_decisions_v7_1400.csv", encoding="utf-8-sig")))

    rng = random.Random(SEED)

    # ---- build one row per decision -----------------------------------------
    items = []
    for d in decisions:
        key = (d["field"], d["component"])
        definition = COMPONENT_DEFINITIONS.get(key) or (d.get("component_definition") or "")
        reg = registry.get(d["record_id"], {})
        items.append(OrderedDict([
            ("record_id_real", d["record_id"]),
            ("field", d["field"]),
            ("component", d["component"]),
            ("component_definition", definition),
            ("title", (reg.get("title") or d.get("title") or "")[:120]),
            ("retained_text", retained_text(reg)),
        ]))

    # ---- randomise order and mask ids ---------------------------------------
    order = list(range(len(items)))
    rng.shuffle(order)

    masked = {}
    rows = []
    for pos, idx in enumerate(order, start=1):
        it = items[idx]
        item_id = f"ITEM_{pos:04d}"
        masked[item_id] = (it["record_id_real"], it["field"], it["component"])
        rows.append(OrderedDict([
            ("item_id", item_id),
            ("item_order", pos),
            ("field", it["field"]),
            ("component", it["component"]),
            ("component_definition", it["component_definition"]),
            ("title", it["title"]),
            ("retained_text_to_review", it["retained_text"]),
            # --- to be filled by the independent coder; written empty ---
            ("coder1_status", ""),
            ("coder1_supporting_quote", ""),
            ("coder1_note", ""),
            ("coder2_status", ""),
            ("coder2_supporting_quote", ""),
            ("coder2_note", ""),
            ("adjudicated_status", ""),
            ("adjudication_reason", ""),
        ]))

    with open(OUT / "blinded_coding_sheet_v8.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    with open(OUT / "sealed_key_v8.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["item_id", "record_id_real", "field", "component"])
        for k, v in masked.items():
            w.writerow([k, v[0], v[1], v[2]])

    with open(OUT / "component_definitions_v8.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["field", "component", "definition", "exclusion_rule"])
        for (fl, cp), dfn in COMPONENT_DEFINITIONS.items():
            w.writerow([fl, cp, dfn, EXCLUSION_RULE])

    # ---- adjudication log template ------------------------------------------
    with open(OUT / "adjudication_log_template_v8.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["item_id", "coder1_status", "coder2_status", "agreement",
                    "adjudicated_status", "adjudicator", "adjudication_reason", "date"])
        for r in rows:
            w.writerow([r["item_id"], "", "", "", "", "", "", ""])

    # ---- protocol ------------------------------------------------------------
    (OUT / "README_blinded_review_protocol_v8.md").write_text(
        PROTOCOL.format(n=len(rows), states=STATES), encoding="utf-8")

    # ---- cross-tabulation template -------------------------------------------
    (OUT / "cross_tabulation_template_v8.md").write_text(CROSSTAB, encoding="utf-8")

    # ---- agreement computation, guarded --------------------------------------
    (OUT / "compute_agreement_v8.py").write_text(COMPUTE_AGREEMENT, encoding="utf-8")

    print(f"wrote {len(rows)} blinded items to {OUT}")
    for p in sorted(OUT.iterdir()):
        print("  ", p.name, p.stat().st_size)


PROTOCOL = r"""# Independent human review protocol (v8)

## Why this exists

The primary audit result was produced by an AI-assisted semantic process with author confirmation of
changed and low-confidence decisions. That design cannot find errors that were never flagged as
uncertain, including false negatives. This package exists so that a human who has **not** seen the
AI labels can recode the corpus under the same frozen rules.

## Status: NOT YET PERFORMED

Every judgement column in `blinded_coding_sheet_v8.csv` is **empty**. No review result, agreement
statistic, or recoded count exists in this release. Those columns must be filled by real human
coders. **Nothing in this package may be pre-filled or estimated**; an invented review record would
be a fabricated result and is worse than no review.

## What the coder receives

`blinded_coding_sheet_v8.csv` — {n} decisions (100 records x 14 components), containing:

- `item_id` — a masked identifier in randomised order (seed 20260924);
- `field`, `component`, `component_definition` — the frozen definition being applied;
- `title` — the record title;
- `retained_text_to_review` — the retained excerpt text for that record.

The sheet **does not contain** the AI label, the AI rationale, the confidence value, the
non-recovery metadata, or the source stratum. The randomisation and masking mean the coder cannot
infer the original ordering or grouping.

## What the coder must do

For each item, assign exactly one of: **{states}**.

Rules:

1. Judge only what is present in `retained_text_to_review`. Do not retrieve the source.
2. A positive label requires a statement in the retained text that meets the component definition.
3. Record in `coder1_supporting_quote` the sentence that supports a positive label.
4. Use `unclear` when the text does not permit a judgement; use `not_applicable` only when there is
   affirmative evidence that no legitimate opportunity existed.
5. Exclusions (from the frozen rule): page navigation; advertisements; recommended or related links;
   headers and footers; unrelated sidebars; generic framework or policy text; taxonomy or
   classification tag blocks; the same words in a sense unrelated to the target event; external
   headlines where only the headline and not the article content is retained.

## Who is needed

At least one independent coder who did not produce the original labels. **Two is required** for any
agreement estimate. Disagreements should be resolved by a third author acting as adjudicator,
recorded in `adjudication_log_template_v8.csv` with a reason per item.

Human judgement is not designated a "gold standard" in the paper. It is an independent recoding, and
disagreement is reported, not suppressed.

## After coding returns

1. Merge coder columns into `blinded_coding_sheet_v8.csv`.
2. Run `python compute_agreement_v8.py`. It refuses to run on an empty or partially filled sheet.
3. The script emits the 2x2 cross-tabulation against the frozen AI-assisted labels, agreement
   counts, and the recoded component and field counts.
4. Report whether the key counts and conclusions changed. Do not select whichever result looks
   better; report both and state which is carried forward as primary.

## Files

| File | Purpose |
|---|---|
| `blinded_coding_sheet_v8.csv` | the coding sheet, judgement columns empty |
| `component_definitions_v8.csv` | the 14 definitions plus the exclusion rule |
| `adjudication_log_template_v8.csv` | disagreement and adjudication record |
| `cross_tabulation_template_v8.md` | the table to fill once coding returns |
| `sealed_key_v8.csv` | masked ID to real record and component |
| `compute_agreement_v8.py` | runs only on a filled sheet |
"""

CROSSTAB = r"""# Cross-tabulation: independent human recoding vs frozen AI-assisted labels

**Status: to be completed after independent human coding.**

## Table A — component decisions (1,400)

| | AI-assisted: supported | AI-assisted: not recovered | Row total |
|---|---|---|---|
| Human: supported | a | b | a+b |
| Human: not recovered | c | d | c+d |
| Column total | a+c | b+d | 1,400 |

Cells to be filled by `compute_agreement_v8.py`.

## Table B — what changed

| Quantity | AI-assisted (frozen) | Independent human | Changed? |
|---|---|---|---|
| Supported component decisions | 215 | | |
| Exposure complete support | 4 | | |
| Exposure partial support | 46 | | |
| Follow-up complete support | 0 | | |
| Follow-up partial support | 29 | | |
| Closure complete support | 0 | | |
| Closure partial support | 21 | | |
| `reopening_rule` supported | 0 | | |

## Table C — agreement

| Statistic | Value |
|---|---|
| Raw agreement | (a+d)/1400 |
| Cohen's kappa | |
| Gwet's AC1 | |
| Disagreements adjudicated | |
| Direction of disagreements | human-positive / AI-negative: b ; AI-positive / human-negative: c |

Report kappa and AC1 together; kappa is unstable when one category dominates.

## Decisions to state in the paper

1. Did the key counts change?
2. Did any conclusion change?
3. Which set is carried forward as primary, and why — stated before results are compared.
"""

COMPUTE_AGREEMENT = r'''# -*- coding: utf-8 -*-
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
'''


if __name__ == "__main__":
    main()
