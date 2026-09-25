# -*- coding: utf-8 -*-
"""
Independent-method re-derivation of all 1,400 component decisions (v8 second-pass audit).

PRINCIPLE
---------
The original labels were produced by semantic judgement. This pass uses a *different
principle*: purely lexical presence testing. It asks only whether the retained text
contains a surface marker of the kind of evidence a component requires. It performs no
semantic judgement, reads no rationale field, and never looks at the original label while
computing.

It is therefore a NECESSARY-CONDITION test, not a sufficient one:
  - probe fires  -> the required kind of text is present; semantic support is possible
  - probe silent -> the required kind of text is absent; semantic support is implausible

Consequence: the probe over-fires. That is intended. Disagreements are adjudicated
separately by reading; the probe is never treated as a correctness oracle.

INDEPENDENCE
------------
Inputs are the record-level retained text in source_registry.csv. The decision-level
`evidence_excerpt` field is deliberately NOT used: it is populated only for the 228
decisions already labelled supported, so auditing not-recovered decisions with it would
be circular.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, OrderedDict
from pathlib import Path

csv.field_size_limit(10 ** 9)

ROOT = Path(__file__).resolve().parent.parent
SUP = ROOT / "02_supplement"
OUT = SUP

# ---------------------------------------------------------------- text assembly
# Retained-text pool. The C1-C10 columns are excluded: they contain only the boilerplate
# "No recoverable public evidence for this candidate capability." and no source text.
TEXT_COLS = [
    "source_excerpt",
    "evidence_excerpt_v25",
    "reverification_excerpt",
    "v29_exposure_denominator_present_evidence_excerpt",
    "v29_follow_up_window_present_evidence_excerpt",
    "v29_closure_basis_present_evidence_excerpt",
]

BOILERPLATE = [
    "No recoverable public evidence for this candidate capability.",
    "Articles about this incident",
]

NAV_CHROME = [
    "Search Search Search", "Skip to content", "Toggle navigation", "Main navigation",
    "You are here", "Breadcrumb", "Cookie", "Subscribe", "Newsletter", "Sign up",
    "Log in", "Read more", "Share this", "Related articles", "Recommended for you",
    "Menu", "Home", "About", "Contact", "Privacy policy", "Terms of use",
    "Live data", "Policies and initiatives", "Priority issues", "Tools & Metrics",
    "AI Policy Toolkit", "WIPS", "Catalogue",
]

OECD_TAXONOMY = [
    "AI principles", "Affected stakeholders", "Harm types", "Industries",
    "Business function", "AI system task", "[AI generated]",
    "Robustness & digital security", "Transparency & explainability",
    "Why's our monitor labelling this an incident or hazard?",
    "Why's our monitor labelling this an incident?",
]

RATIONALE_MARKERS = [
    "the event fits the definition of", "fits the definition of an AI incident",
    "fits the definition of an AI hazard", "our monitor labelling",
]

# The retained-text pool also carries the audit's OWN annotation boilerplate, which is
# not source text and must not be probed. Found during adjudication of the first run.
AUDIT_ANNOTATION_PATTERNS = [
    r"public-source limitation:[^~]*",
    r"URL recheck failed;[^~]*",
    r"URL recheck failed[^~]*",
    r"inherited local snapshot retained without upgrading source status",
]


def clean(text: str) -> str:
    """Strip material the component definition explicitly excludes."""
    t = text or ""
    for marker in BOILERPLATE:
        t = t.split(marker)[0]          # drop the outbound article rail
    for phrase in NAV_CHROME + OECD_TAXONOMY + RATIONALE_MARKERS:
        t = t.replace(phrase, " ")
    for pat in AUDIT_ANNOTATION_PATTERNS:
        t = re.sub(pat, " ", t)
    return re.sub(r"\s+", " ", t)


def record_text(row: dict) -> str:
    parts = [clean(row.get(c, "")) for c in TEXT_COLS]
    seen, uniq = set(), []
    for p in parts:
        if p and p not in seen:
            seen.add(p)
            uniq.append(p)
    return " ".join(uniq)


# ---------------------------------------------------------------- lexical probes
# Each probe: list of regex alternatives. Probe fires if ANY alternative matches.
# These encode "surface marker of the required kind of evidence", nothing more.

NUM = r"(?:\d[\d,\.]*|\bone\b|\btwo\b|\bthree\b|\bfour\b|\bfive\b|\bsix\b|\bseven\b|\beight\b|\bnine\b|\bten\b|\bhundreds?\b|\bthousands?\b|\bmillions?\b)"

PROBES: "OrderedDict[str, list]" = OrderedDict([

    ("exposure|unit", [
        r"\bevery (?:person|resident|user|patient|employee|student|applicant|customer|driver|worker)\b",
        r"\ball (?:persons|residents|users|patients|employees|students|applicants|customers|drivers|workers)\b",
        r"\beach (?:person|resident|user|patient|employee|student|applicant)\b",
        r"\b(?:persons|people|individuals|residents|users|patients|employees|students|applicants|customers|workers|drivers)\s+(?:who|that|whose)\b",
        r"\b" + NUM + r"\s+(?:people|persons|individuals|residents|users|patients|employees|students|applicants|workers|customers|drivers|cases|incidents)\b",
        r"\bthe (?:system|algorithm|model|tool|program|software|app|platform|device)\s+(?:was|is|has been|had been)\b",
        r"\brisk scorer?\b", r"\bwas assigned a\b", r"\bwere assigned\b", r"\bscored\b",
    ]),

    ("exposure|eligibility", [
        r"\beligib\w+", r"\bqualif\w+", r"\bcriteri\w+", r"\binclusion criteri\w+",
        r"\bexclusion criteri\w+", r"\bthreshold\b", r"\bonly (?:those|persons|applicants|candidates)\b",
        r"\bmust (?:be|have)\b", r"\brequired to\b", r"\bentitled to\b", r"\became eligible\b",
        r"\bmeet(?:s|ing)? the (?:requirements|conditions|criteria)\b",
        r"\banyone who\b", r"\bwhoever\b", r"\bif .{0,40}\bthen\b",
    ]),

    ("exposure|time_origin", [
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}?,?\s*\d{4}\b",
        r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
        r"\b(?:19|20)\d{2}\b",
        r"\bsince\s+(?:19|20)\d{2}\b", r"\bfrom\s+(?:19|20)\d{2}\b",
        r"\bbetween\s+(?:19|20)\d{2}\s+and\b", r"\bfrom .{0,30}\b(?:onwards|onward)\b",
        r"\b(?:began|begun|started|commenced|launched|introduced|deployed|rolled out|implemented)\s+(?:in|on|from)\b",
        r"\bin\s+(?:19|20)\d{2}\b", r"\bdate of\b", r"\badopted\b", r"\bpublished\b",
    ]),

    ("exposure|coverage", [
        r"\b\d{1,3}(?:\.\d+)?\s?%", r"\bpercent(?:age)?\b", r"\bproportion\b", r"\bshare of\b",
        r"\bout of\s+" + NUM, r"\bof (?:the\s+)?" + NUM + r"\s+(?:people|persons|cases|records|rows|applicants|users)\b",
        r"\bcoverage\b", r"\bN\s?=\s?\d+", r"\bn\s?=\s?\d+", r"\bsample of\s+" + NUM,
        r"\btotal of\s+" + NUM, r"\ba total of\s+" + NUM, r"\bcomprehensive\b", r"\ball\s+" + NUM,
        r"\bnationally\b", r"\bacross the (?:country|state|city|system)\b",
    ]),

    ("follow_up|calendar_interval", [
        r"\b\d+\s+(?:days?|weeks?|months?|years?)\b",
        r"\b(?:daily|weekly|monthly|quarterly|annual(?:ly)?|yearly)\b",
        r"\bfollow[- ]?up\b", r"\bafter\s+" + NUM + r"\s+(?:days?|weeks?|months?|years?)\b",
        r"\bwithin\s+" + NUM + r"\s+(?:days?|weeks?|months?|years?)\b",
        r"\bover (?:a|the) (?:period|course) of\b", r"\binterval\b", r"\bperiod of\b",
        r"\bbetween\s+.{0,40}\band\s+.{0,40}\b", r"\blater\b", r"\bsubsequent\w*\b",
        r"\bmonths? later\b", r"\byears? later\b", r"\bdays? later\b",
    ]),

    ("follow_up|exposure_qualified_observation", [
        r"\b(?:found|observed|detected|identified|reported|showed|shown|revealed|measured|documented|confirmed|established)\b.{0,80}\b(?:that|the|a|an)\b",
        r"\b(?:investigation|review|audit|inquiry|assessment|analysis)\s+(?:found|showed|revealed|concluded|identified)\b",
        r"\baccording to\b.{0,60}\b(?:report|data|records|documents|footage)\b",
        r"\bre-?examined\b", r"\breviewed\b", r"\bmonitor(?:ed|ing)\b", r"\btracked\b",
        r"\baudit\b", r"\bwas later\b", r"\bafter the\b.{0,40}\bshowed\b",
    ]),

    ("follow_up|trace_coverage", [
        r"\blogs?\b", r"\baudit trail\b", r"\brecords?\b", r"\bdatabase\b", r"\bdataset\b",
        r"\bdata set\b", r"\bregistry\b", r"\bregisters?\b", r"\btrac(?:e|es|ing)\b",
        r"\bfootage\b", r"\bCCTV\b", r"\bcamera\b", r"\bmetadat	a\b", r"\bmetadata\b",
        r"\bmonitoring (?:system|data|records)\b", r"\bdocumentation\b",
        r"\bkept (?:a )?record\b", r"\bstored\b", r"\bretained\b",
    ]),

    ("follow_up|owner", [
        r"\b(?:by|from)\s+the\s+\w+\s+(?:department|agency|office|authority|commission|board|court|police|company|regulator|ministry|tribunal)\b",
        r"\b(?:department|agency|office|authority|commission|board|court|police|regulator|ministry|tribunal|inspector\w*)\b",
        r"\b(?:investigator|investigators|officer|officers|reviewer|reviewers|auditor|team|unit|division|task ?force)\b",
        r"\b(?:NTSB|ICO|FTC|EEOC|FCC|HHS|FDA|DPA|CNIL)\b",
        r"\bpolice\b", r"\bregulator\b", r"\bcourt\b", r"\bcommission(?:er)?\b",
    ]),

    ("closure|scope", [
        r"\bthe (?:scope|matter|case|issue|complaint|investigation)\s+(?:of|covers|concerns|regarding)\b",
        r"\b(?:regarding|concerning|in relation to|with respect to|pertaining to|applies to|covers)\b",
        r"\bthe (?:decision|ruling|judgment|judgement|order|notice|determination)\s+(?:covers|applies|concerns|relates)\b",
        r"\b(?:all|only|specifically)\s+(?:facilities|sites|offices|centres|centers|locations|users|employees)\b",
        r"\bscope\b",
    ]),

    ("closure|evidence_basis", [
        r"\baccording to\b", r"\bbased on\b", r"\bon the basis of\b", r"\bevidence\b",
        r"\bfindings?\b", r"\bconcluded?\b", r"\bfound that\b", r"\bdetermined that\b",
        r"\binvestigation\b", r"\breport\b", r"\bdocuments?\b", r"\bfootage\b",
        r"\bdata\s+(?:show|shows|showed|indicate)\w*\b", r"\btestimony\b", r"\bexpert\b",
        r"\bstatements?\b", r"\bsubmissions?\b",
    ]),

    ("closure|date", [
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}?,?\s*\d{4}\b",
        r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
        r"\b\d{4}-\d{2}-\d{2}\b", r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
        r"\b(?:19|20)\d{2}\b", r"\bdate[d:]?\s*\d", r"\bpublished\b", r"\bissued\b",
        r"\badopted\b", r"\bhanded down\b", r"\bordered\b", r"\bconcluded on\b",
    ]),

    ("closure|owner", [
        r"\b(?:by|from)\s+the\s+\w+\s+(?:department|agency|office|authority|commission|board|court|police|company|regulator|ministry|tribunal)\b",
        r"\b(?:department|agency|office|authority|commission|board|court|police|regulator|ministry|tribunal|commissioner|inspector\w*)\b",
        r"\b(?:NTSB|ICO|FTC|EEOC|FCC|HHS|FDA|DPA|CNIL)\b",
        r"\bordered\b", r"\bfined\b", r"\bsanctioned\b", r"\breprimanded\b",
        r"\benforcement (?:notice|action)\b", r"\bjudgment\b", r"\bjudgement\b",
        r"\bruling\b", r"\bdecision\b", r"\bpenalty\b",
    ]),

    ("closure|uncertainty", [
        r"\bunclear\b", r"\bunknown\b", r"\bnot (?:determined|established|known|resolved|disclosed)\b",
        r"\bremains?\b", r"\bunresolved\b", r"\bpending\b", r"\bongoing\b", r"\bfurther\b",
        r"\bhowever\b", r"\bcannot\b", r"\bcould not\b", r"\bdid not (?:establish|determine|disclose)\b",
        r"\bopen question\b", r"\bno (?:final|definitive)\b", r"\bappears? to\b",
        r"\ballegedly\b", r"\breportedly\b", r"\bdisputed\b",
    ]),

    ("closure|reopening_rule", [
        r"\bre-?open\w*", r"\bre-?opening\b", r"\bappeal\w*", r"\breconsider\w*",
        r"\brequest a review\b", r"\bpetition\b", r"\bif new (?:evidence|information)\b",
        r"\btrigger\b", r"\bmay be (?:re-?opened|revised|reviewed)\b",
        r"\bsubject to review\b", r"\bsubject to appeal\b", r"\breview (?:process|procedure|mechanism)\b",
        r"\bfurther review\b", r"\bright to appeal\b", r"\bshall be reviewed\b",
        r"\bwill be (?:reviewed|re-?assessed|re-?evaluated)\b", r"\bre-?assess\w*", r"\bre-?evaluat\w*",
    ]),
])


def probe(text: str, patterns: list, flags=re.I) -> tuple:
    """Return (fired, matched_markers)."""
    hits = []
    for p in patterns:
        m = re.search(p, text, flags)
        if m:
            frag = m.group(0)
            frag = frag if len(frag) <= 70 else frag[:70] + "..."
            hits.append(frag.strip())
    return (len(hits) > 0), hits[:6]


# ---------------------------------------------------------------- main


def main() -> None:
    reg = {r["record_id"]: r for r in csv.DictReader(open(SUP / "source_registry.csv", encoding="utf-8-sig"))}
    dec = list(csv.DictReader(open(SUP / "component_decisions_v7_1400.csv", encoding="utf-8-sig")))

    # Cache cleaned text per record
    text_cache = {rid: record_text(r) for rid, r in reg.items()}
    stratum = {rid: r["source_stratum"] for rid, r in reg.items()}

    rows = []
    for d in dec:
        rid = d["record_id"]
        key = d["field"] + "|" + d["component"]
        patterns = PROBES.get(key)
        if patterns is None:
            raise KeyError("no probe defined for " + key)
        txt = text_cache.get(rid, "")
        fired, hits = probe(txt, patterns)
        rows.append(OrderedDict([
            ("record_id", rid),
            ("case_id", d["case_id"]),
            ("source_stratum", stratum.get(rid, "")),
            ("field", d["field"]),
            ("component", d["component"]),
            ("semantic_status", d["component_status"]),
            ("semantic_primary_status", d["v6_primary_support_status"]),
            ("retained_text_chars", len(txt)),
            ("mechanical_probe_fired", "yes" if fired else "no"),
            ("matched_markers", " | ".join(hits)),
        ]))

    with open(OUT / "independent_mechanical_redecode_v8.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # ---- cross-tabulation (computed only after all probes are fixed) ----
    cross = {}
    for key in PROBES:
        sub = [r for r in rows if r["field"] + "|" + r["component"] == key]
        c = Counter((r["semantic_status"], r["mechanical_probe_fired"]) for r in sub)
        cross[key] = {
            "n": len(sub),
            "sem_supported_probe_fired": c.get(("supported", "yes"), 0),
            "sem_supported_probe_silent": c.get(("supported", "no"), 0),
            "sem_notrecovered_probe_fired": c.get(("not_recovered", "yes"), 0),
            "sem_notrecovered_probe_silent": c.get(("not_recovered", "no"), 0),
        }

    cand_fn = [r for r in rows
               if r["semantic_status"] == "not_recovered" and r["mechanical_probe_fired"] == "yes"]
    cand_fp = [r for r in rows
               if r["semantic_status"] == "supported" and r["mechanical_probe_fired"] == "no"]

    summary = OrderedDict([
        ("release", "v8 second-pass audit"),
        ("method", "lexical presence probe on record-level retained text; no semantic judgement; "
                   "no rationale or label field read during probe computation"),
        ("independence_note", "different principle from the original semantic coding; the same agent "
                              "implemented both, so this is method triangulation, not rater independence"),
        ("text_source", "union of 6 retained-excerpt columns in source_registry.csv; C1-C10 columns "
                        "excluded (boilerplate only); decision-level evidence_excerpt deliberately unused "
                        "because it is populated only for already-supported decisions"),
        ("exclusions_applied", "outbound article rail, nav chrome, OECD taxonomy tag blocks, "
                               "monitor classification rationale, 'No recoverable public evidence' boilerplate"),
        ("n_decisions", len(rows)),
        ("probe_is", "necessary-condition test; over-fires by design; not a correctness oracle"),
        ("cross_tabulation_by_component", cross),
        ("candidate_false_negatives", {
            "definition": "semantic=not_recovered AND mechanical probe fired",
            "n": len(cand_fn),
            "by_component": dict(Counter(r["field"] + "|" + r["component"] for r in cand_fn)),
            "by_stratum": dict(Counter(r["source_stratum"] for r in cand_fn)),
        }),
        ("candidate_false_positives", {
            "definition": "semantic=supported AND mechanical probe silent",
            "n": len(cand_fp),
            "by_component": dict(Counter(r["field"] + "|" + r["component"] for r in cand_fp)),
        }),
        ("reopening_rule_focus", {
            "semantic_supported": cross["closure|reopening_rule"]["sem_supported_probe_fired"],
            "probe_fired_while_not_recovered": cross["closure|reopening_rule"]["sem_notrecovered_probe_fired"],
            "note": "closure complete support = 0/100 rests on reopening_rule = 0/100; "
                    "these rows are the highest-priority adjudication target",
        }),
    ])

    with open(OUT / "independent_mechanical_redecode_v8.json", "w", encoding="utf8") as fh:
        json.dump(summary, fh, indent=1, ensure_ascii=False)

    # print concise report
    print(f"{'component':42s} {'n':>4s} {'S+':>4s} {'S-':>4s} {'N+':>4s} {'N-':>4s}")
    for k, v in cross.items():
        print(f"{k:42s} {v['n']:4d} {v['sem_supported_probe_fired']:4d} "
              f"{v['sem_supported_probe_silent']:4d} {v['sem_notrecovered_probe_fired']:4d} "
              f"{v['sem_notrecovered_probe_silent']:4d}")
    print()
    print("candidate false negatives (sem=not_recovered, probe fired):", len(cand_fn))
    print("candidate false positives (sem=supported, probe silent):", len(cand_fp))
    print()
    print("reopening_rule:", json.dumps(summary["reopening_rule_focus"], ensure_ascii=False))
    print()
    print("cand FN by stratum:", dict(Counter(r["source_stratum"] for r in cand_fn)))
    print("written:",
          OUT / "independent_mechanical_redecode_v8.csv",
          OUT / "independent_mechanical_redecode_v8.json")


if __name__ == "__main__":
    main()
