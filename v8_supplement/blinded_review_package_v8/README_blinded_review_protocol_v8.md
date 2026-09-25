# Independent human review protocol (v8)

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

`blinded_coding_sheet_v8.csv` — 1400 decisions (100 records x 14 components), containing:

- `item_id` — a masked identifier in randomised order (seed 20260924);
- `field`, `component`, `component_definition` — the frozen definition being applied;
- `title` — the record title;
- `retained_text_to_review` — the retained excerpt text for that record.

The sheet **does not contain** the AI label, the AI rationale, the confidence value, the
non-recovery metadata, or the source stratum. The randomisation and masking mean the coder cannot
infer the original ordering or grouping.

## What the coder must do

For each item, assign exactly one of: **supported | not_recovered | unclear | not_applicable**.

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
