# -*- coding: utf-8 -*-
"""
OECD AIM retained-material sufficiency audit (v8).

Reviewer point 2: all 280 OECD AIM component decisions were "not_recovered",
and every one of the 280 evidence_excerpt cells was empty. This re-opens the
retained bundle and asks, for each record, what kind of text was actually kept.

## Classification rule (applied identically to all 100 rows)

For each of six retained excerpt fields:

1. strip the leading record title (scraped pages embed it);
2. truncate at "Articles about this incident or hazard" (the outbound link rail);
3. delete literal site-chrome and OECD-AIM taxonomy marker phrases;
4. from the residue, compute
      overlap  = |title content words present in residue| / |title content words|
      sentences = number of clauses >=40 characters ending in . ! or ?
   where a content word is an alphabetic token of >=4 characters, excluding a
   closed stopword list.

`incident_narrative` requires overlap >= 0.30 AND sentences >= 1.
The rationale is that a retained text counts as assessable only if it is still
about the incident named in the title after site furniture is removed.

Outputs (02_supplement/):
  OECD_AIM_retention_audit_v8.csv          - 20 OECD records, per-record detail
  retained_material_class_by_record_v8.csv - all 100 rows, same rule
  OECD_AIM_retention_audit_v8.json         - machine-readable summary
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

csv.field_size_limit(10 ** 9)

FROZEN_LOCAL = Path(__file__).resolve().parent.parent / "02_supplement"
FROZEN_V7 = Path(r"C:/Users/fengq/Desktop/AI健康医学_Applied_Sciences_v7_20260920_175106/02_supplement")
# Prefer the copies bundled with this release so v8 is self-contained;
# fall back to the original v7 location if they are absent.
V7 = FROZEN_LOCAL if (FROZEN_LOCAL / "source_registry.csv").exists() else FROZEN_V7
V8 = Path(__file__).resolve().parent.parent / "02_supplement"
V8.mkdir(parents=True, exist_ok=True)

# ---- vocabularies -----------------------------------------------------------
STOP = {
    "with", "that", "this", "from", "have", "been", "were", "their", "which",
    "would", "about", "after", "into", "over", "more", "than", "other", "some",
    "such", "only", "also", "when", "what", "will", "could", "there", "them",
    "then", "these", "those", "using", "used", "into", "onto", "upon",
}

NAV_MARKERS = [
    "Live data", "Policies and initiatives", "Priority issues", "Tools",
    "Resources", "About", "Search", "Catalogue", "Tools & Metrics", "WIPS",
    "AI Policy Toolkit", "Menu", "Subscribe", "Newsletter", "Cookie",
    "Skip to main content", "Read more", "See also",
]

TAXONOMY_MARKERS = [
    "AI principles", "Affected stakeholders", "Harm types", "Industries",
    "Business function", "AI system task", "[AI generated]",
    "Robustness & digital security", "Transparency & explainability",
]

LINK_RAIL = "Articles about this incident"

# Text that is about the source rather than drawn from it, or that is site
# boilerplate, is excluded before any narrative test is applied.
META_MARKERS = ["public-source limitation:"]
DISCLAIMER_MARKERS = [
    "should not be reported as representing",
    "The information displayed in the AIM",
]

SENTENCE = re.compile(r"[A-Za-z][^.!?]{40,}[.!?]")
WORD = re.compile(r"[A-Za-z]{4,}")


def content_words(text: str) -> set[str]:
    return {w.lower() for w in WORD.findall(text or "")} - STOP


def residue(excerpt: str, title: str) -> str:
    t = excerpt or ""
    if title and t.lower().startswith(title.lower()[:40]):
        t = t[len(title):]
    t = re.split(LINK_RAIL, t, maxsplit=1)[0]
    for m in NAV_MARKERS + TAXONOMY_MARKERS:
        t = t.replace(m, " ")
    return t


def classify(excerpt: str, title: str) -> tuple[str, float, int]:
    """Return (class, title_overlap, sentence_count)."""
    t = excerpt or ""
    # Exclusions checked first: these are never incident narrative.
    if any(m.lower() in t.lower() for m in META_MARKERS):
        return "meta_note", 0.0, 0
    if any(m.lower() in t.lower() for m in DISCLAIMER_MARKERS):
        return "site_disclaimer", 0.0, 0
    if not t.strip():
        return "empty", 0.0, 0
    tc = content_words(title)
    if not tc:
        return "no_title_content_words", 0.0, 0
    res = residue(excerpt, title)
    if not res.strip():
        return "chrome_only", 0.0, 0
    ov = len(tc & content_words(res)) / len(tc)
    ns = len(SENTENCE.findall(res))
    if ov >= 0.30 and ns >= 1:
        return "incident_narrative", round(ov, 2), ns
    if ov >= 0.30:
        return "incident_fragments", round(ov, 2), ns
    if ns >= 1:
        return "non_incident_prose", round(ov, 2), ns
    return "chrome_or_metadata_only", round(ov, 2), ns


EXCERPT_FIELDS = OrderedDict([
    ("source_excerpt", "source_excerpt"),
    ("evidence_excerpt_v25", "evidence_excerpt_v25"),
    ("reverification_excerpt", "reverification_excerpt"),
    ("v29_exposure_excerpt", "v29_exposure_denominator_present_evidence_excerpt"),
    ("v29_follow_up_excerpt", "v29_follow_up_window_present_evidence_excerpt"),
    ("v29_closure_excerpt", "v29_closure_basis_present_evidence_excerpt"),
])

NARRATIVE_CLASSES = {"incident_narrative", "incident_fragments"}

# ---------------------------------------------------------------------------
# Manual adjudication of all 20 OECD AIM records.
#
# Every record was read directly. The retained bundle was found to consist of
# four text types:
#   (a) OECD AIM taxonomy tag block - "[AI generated] AI principles ... Industries
#       ... Affected stakeholders ... Harm types ..."
#   (b) external article headline + date + outlet + "Why's our monitor labelling
#       this an incident or hazard?" - a pointer, not content; often non-English
#   (c) the monitor's own classification rationale - "the event fits the
#       definition of an AI Hazard"
#   (d) incident narrative
# Only (d) is assessable. Adjudication below is by reading, not by classifier.
# ---------------------------------------------------------------------------
MANUAL_ADJUDICATION = {
    "V25R051": "no narrative - taxonomy (a) + headline (b)",
    "V25R052": "no narrative - headline (b) + taxonomy (a) + hazard rationale (c)",
    "V25R053": "narrative (d) - taxi entered crime scene; zero defensible",
    "V25R054": "partial narrative (d) - summary of what the article states",
    "V25R055": "no narrative - headlines (b) + taxonomy (a)",
    "V25R056": "no narrative - taxonomy (a) only, all three fields",
    "V25R057": "no narrative - taxonomy (a) + headline (b)",
    "V25R058": "no narrative - taxonomy (a) only, all three fields",
    "V25R059": "no narrative - taxonomy (a) + hazard rationale (c)",
    "V25R060": "no narrative - headline (b) + taxonomy (a)",
    "V25R081": "no narrative - taxonomy (a) + Persian headline (b)",
    "V25R082": "no narrative - Italian headline (b) + taxonomy (a)",
    "V25R083": "no narrative - taxonomy (a) + AIM site/disclaimer text",
    "V25R084": "narrative (d) - OpenAI alerted authorities, arrest followed",
    "V25R085": "no narrative - taxonomy (a) only, all three fields",
    "V25R086": "no narrative - taxonomy (a) + Chinese headline (b)",
    "V25R087": "no narrative - headlines (b) only, no article content",
    "V25R088": "no narrative - taxonomy (a) only, all three fields",
    "V25R089": "narrative (d) - court sanction described; CANDIDATE FALSE NEGATIVE",
    "V25R090": "no narrative - taxonomy (a) + hazard rationale (c)",
}
# Records whose retained material is sufficient to assess the component rules.
MANUALLY_ASSESSABLE = {"V25R053", "V25R054", "V25R084", "V25R089"}


def stratum_of(case_id: str) -> str:
    if case_id.startswith("AIID"):
        return "AIID"
    if case_id.startswith("OECD"):
        return "OECD AIM"
    return "direct source"


def main() -> int:
    registry = list(csv.DictReader(open(V7 / "source_registry.csv", encoding="utf-8-sig")))
    decisions = list(csv.DictReader(open(V7 / "component_decisions_v7_1400.csv", encoding="utf-8-sig")))

    by_rec: dict[str, list[dict]] = defaultdict(list)
    for d in decisions:
        by_rec[d["record_id"]].append(d)

    rows_out: list[OrderedDict] = []
    for r in registry:
        rec_id, case_id = r["record_id"], r["case_id"]
        title = r.get("title") or ""
        detail: dict[str, str] = {}
        narrative_fields: list[str] = []
        for short, col in EXCERPT_FIELDS.items():
            c, ov, ns = classify(r.get(col, ""), title)
            detail[short] = c
            if c in NARRATIVE_CLASSES:
                narrative_fields.append(short)

        if narrative_fields:
            primary = "incident_narrative"
        else:
            primary = "no_incident_narrative"

        decs = by_rec.get(rec_id, [])
        # component_status in the v7 release file is the boundary-inclusive status
        recorded_supported = sum(1 for d in decs if d.get("component_status") == "supported")
        recorded_excerpt_nonempty = sum(1 for d in decs if (d.get("evidence_excerpt") or "").strip())

        row = OrderedDict([
            ("record_id", rec_id),
            ("case_id", case_id),
            ("source_stratum", stratum_of(case_id)),
            ("historical_selection_cohort", r.get("historical_selection_cohort", "")),
            ("title", title[:90]),
            ("url_check_status", r.get("url_check_status", "")),
            ("source_relationship", r.get("source_relationship", "")),
            ("retained_material_primary_class", primary),
            ("fields_with_incident_narrative", "; ".join(narrative_fields) or "none"),
            ("manual_adjudication", MANUAL_ADJUDICATION.get(rec_id, "not_adjudicated")),
        ])
        for k, v in detail.items():
            row[f"class_{k}"] = v
        row["recorded_supported_components_of_14"] = recorded_supported
        row["recorded_evidence_excerpt_nonempty_of_14"] = recorded_excerpt_nonempty
        row["reading_of_zero"] = (
            "not_recovered" if (rec_id in MANUALLY_ASSESSABLE and recorded_supported == 0)
            else "retained_material_insufficient" if recorded_supported == 0
            else "n/a")
        row["non_recovery_cause_status"] = decs[0].get("non_recovery_cause_status", "") if decs else ""
        rows_out.append(row)

    for path in ("retained_material_class_by_record_v8.csv",):
        with open(V8 / path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
            w.writeheader()
            w.writerows(rows_out)

    oecd = [r for r in rows_out if r["source_stratum"] == "OECD AIM"]
    with open(V8 / "OECD_AIM_retention_audit_v8.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(oecd[0].keys()))
        w.writeheader()
        w.writerows(oecd)

    summary = {
        "release": "v8",
        "question": ("For each OECD AIM record, does the retained bundle contain incident "
                     "narrative sufficient to support a not-recovered judgement, or only "
                     "material insufficient to assess?"),
        "rule": ("Per retained field: strip leading title; truncate at the outbound article "
                 "rail; delete site-chrome and OECD-AIM taxonomy marker phrases; require "
                 "title content-word overlap >= 0.30 AND >=1 sentence of >=40 characters. "
                 "Identical rule applied to all 100 rows in all three strata."),
        "threshold": {"title_overlap_min": 0.30, "min_sentence_chars": 40},
        "n_records": len(rows_out),
        "records_with_incident_narrative_by_stratum": {
            s: f"{sum(1 for r in rows_out if r['source_stratum'] == s and r['retained_material_primary_class'] == 'incident_narrative')}"
               f"/{sum(1 for r in rows_out if r['source_stratum'] == s)}"
            for s in ("AIID", "OECD AIM", "direct source")
        },
        "oecd_n": len(oecd),
        "oecd_reading_of_zero": dict(Counter(r["reading_of_zero"] for r in oecd)),
        "oecd_manual_adjudication": {
            "records_read_directly": 20,
            "retained_material_sufficient_to_assess": sorted(MANUALLY_ASSESSABLE),
            "n_assessable": len(MANUALLY_ASSESSABLE),
            "n_insufficient": len(oecd) - len(MANUALLY_ASSESSABLE),
            "retained_text_types_observed": {
                "a_oecd_aim_taxonomy_tag_block": "[AI generated] AI principles / Industries / Affected stakeholders / Harm types",
                "b_external_headline_and_link": "headline + date + outlet + \"Why's our monitor labelling this an incident or hazard?\"",
                "c_monitor_classification_rationale": "e.g. 'the event fits the definition of an AI Hazard'",
                "d_incident_narrative": "substantive description of what happened",
            },
            "non_english_headlines_observed": ["Persian (V25R081)", "Italian (V25R082)",
                                               "Portuguese (V25R084)", "Chinese (V25R086)"],
        },
        "oecd_records_with_zero_recorded_evidence_excerpt": sum(
            1 for r in oecd if r["recorded_evidence_excerpt_nonempty_of_14"] == 0),
        "candidate_false_negative": {
            "record_id": "V25R089",
            "case_id": "OECD09",
            "retained_text": ("A Connecticut plaintiff, Matthew Elliott, was sanctioned after "
                              "embedding hidden AI prompt injections in court filings, aiming to "
                              "manipulate any AI system reviewing the documents."),
            "issue": ("Describes a court sanction, i.e. a disposition, yet all six closure "
                      "components were recorded as not supported."),
            "status": "flagged for independent human review; not adjudicated here",
        },
    }
    with open(V8 / "OECD_AIM_retention_audit_v8.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)

    print(json.dumps(summary, ensure_ascii=False, indent=1))
    print("\nOECD per-record:")
    for r in oecd:
        print(f"  {r['record_id']} {r['case_id']:6s} {r['retained_material_primary_class']:20s} "
              f"narr={r['fields_with_incident_narrative'][:34]:34s} "
              f"sup={r['recorded_supported_components_of_14']} "
              f"exc={r['recorded_evidence_excerpt_nonempty_of_14']} "
              f"-> {r['reading_of_zero']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
