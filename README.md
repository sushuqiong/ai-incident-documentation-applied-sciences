# AI incident documentation audit: reproducibility archive

Public, privacy-minimised archive for the manuscript *Distinguishing Undocumented
from Unretained Evidence: A 100-Record Audit of Public AI-Incident Records across
Three Source Strata, with a Reproducible Evidence-Log Companion*.

- Repository: https://github.com/sushuqiong/ai-incident-documentation-applied-sciences
- Zenodo concept DOI (all versions): https://doi.org/10.5281/zenodo.22845068
- Current version: **v8.0.0** (https://doi.org/10.5281/zenodo.22953653) — `v8_supplement/`, `v8_build/`. Superseded: v6.0.0 (https://doi.org/10.5281/zenodo.22845069), root-level files.

---

## v8.0.0

### What is inside

`v8_supplement/` — frozen analysis inputs and per-decision outputs. Every table,
figure and count in the manuscript is generated from these files.

| File | Content |
|---|---|
| `Supplementary_Table_S1.csv` | the 100 retained record rows |
| `source_registry.csv` | source registry with retained excerpts and surrogate locators |
| `component_decisions_v7_1400.csv` | 1,400 record-component decisions (labels unchanged since v7; v8 did not recode the corpus) |
| `field_states_v7_300.csv` | 300 field states |
| `statistics_v7.json` | frozen strict and minimal-core statistics, both alternative denominators |
| `OECD_AIM_retention_audit_v8.{csv,json}` | retained-material sufficiency audit, OECD AIM stratum (20 records) |
| `retained_material_class_by_record_v8.csv` | retained text class per record |
| `design_requirement_provenance_v8.csv` | audit-to-design traceability with provenance labels |
| `independent_mechanical_redecode_v8.{csv,json}` | full-population lexical re-derivation of all 1,400 decisions |
| `adjudication_scenarios_v8.json` | adjudication scenario results (base / +6 / upper bound) |
| `second_pass_agreement_v8.json` | blinded second-pass agreement (n = 120) |
| `second_pass_disagreements_v8.csv` | the 19 disagreement records |
| `synthetic_task_test_outputs_v8.json` | T01-T11 synthetic test outputs |
| `blinded_review_package_v8/` | 1,400 decisions in randomised order with masked identifiers and **empty judgement columns**; `compute_agreement_v8.py` refuses to run until they are filled |

`v8_build/` — the scripts that generate the manuscript's numbers, figures and
submission artefacts (audit, recoding, agreement, figure and document builds),
plus the synthetic-test expected outputs.

### Privacy minimisation applied to this public copy

Consistent with the v6.0.0 public archive, this release excludes direct source
locators and long source text:

1. `source_url` / `secondary_source_url` are replaced by irreversible surrogates
   `SRC-001`…`SRC-111`. `source_url_map_sha256_v8.csv` gives the SHA-256 prefix of
   each removed locator, so correspondence can be verified without recovering it.
2. Any remaining http(s) URL in any other field is replaced by `[URL-REMOVED]`.
3. Long free-text fields (chiefly in `source_registry.csv`) are truncated at 300
   characters and marked `…[truncated for public release]`.
4. Fields that carry a coding decision, its justification, or the text a coder
   must read to make one (`*_evidence_excerpt`, `*rationale*`,
   `retained_text_to_review`, all of `component_definitions_v8.csv`) are **not**
   truncated, so the blinded package remains usable.

`redaction_log_v8.json` records, per file, how many cells were altered.

### What can and cannot be reproduced from this copy

- **Can be verified directly**: every count in the manuscript (component statuses,
  field states, `statistics_v7.json`, the OECD stratum classification results, the
  adjudication scenarios, the second-pass agreement statistics) and the synthetic
  representational tests T01-T11.
- **Cannot be reproduced from this copy alone**: scripts that re-read the full
  retained source text — chiefly `v8_build/independent_mechanical_redecode_v8.py`
  and `v8_build/audit_oecd_retention_v8.py` — will return different candidate sets
  against truncated text. The reported outputs of those runs are preserved as
  files in `v8_supplement/`; re-running them requires the unredacted supplement,
  which is submitted with the manuscript and is available from the authors on
  request.

### What this archive is not

It is not a validated governance system and supports no accuracy, comparison or
performance claim. The synthetic tests demonstrate representational feasibility on
a frozen synthetic payload only. The semantic component labels were produced by an
AI-assisted procedure confirmed by the authors; no independent human coding has
been performed, and the blinded package is released so that it can be.

---

## v6.0.0 (superseded, root-level files)

Privacy-minimised archive for `AS-v6-20260919_200341`. Contains 1,400 minimal
component labels, 300 derived field states, statistics, schemas, synthetic inputs
and expected outputs, tests, and a one-command verifier (`python verify_release.py`).
Retained for provenance only; it does not generate the numbers in the current
manuscript.

---

## Licence and redistribution

MIT for original code and derived minimal tables (see `LICENSE`); it does not
relicense third-party source material. CC-BY-4.0 applies to the associated written
work. Longer source text and complete webpages are deliberately not redistributed;
only short, purpose-limited excerpts are retained. No patient-level clinical data
or direct personal identifiers were used as analytic variables.
