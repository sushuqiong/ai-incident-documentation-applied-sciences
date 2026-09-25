# Cross-tabulation: independent human recoding vs frozen AI-assisted labels

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
