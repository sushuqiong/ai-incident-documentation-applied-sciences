# -*- coding: utf-8 -*-
"""Dump compact context windows for manual adjudication of candidate false negatives."""
import csv, re, sys
from pathlib import Path
csv.field_size_limit(10**9)
SUP = Path(__file__).resolve().parent.parent / "02_supplement"
reg = {r["record_id"]: r for r in csv.DictReader(open(SUP/"source_registry.csv", encoding="utf-8-sig"))}
red = list(csv.DictReader(open(SUP/"independent_mechanical_redecode_v8.csv", encoding="utf-8-sig")))
COLS = ['source_excerpt','evidence_excerpt_v25','reverification_excerpt',
        'v29_exposure_denominator_present_evidence_excerpt',
        'v29_follow_up_window_present_evidence_excerpt',
        'v29_closure_basis_present_evidence_excerpt']
want = sys.argv[1:]
out = []
for r in red:
    if r["mechanical_probe_fired"] != "yes": continue
    if r["semantic_status"] != "not_recovered": continue
    if want and r["component"] not in want: continue
    rid = r["record_id"]; reg1 = reg[rid]
    blob = " ~ ".join((reg1.get(c) or "") for c in COLS)
    mk = r["matched_markers"].split(" | ")[0]
    m = re.search(re.escape(mk), blob, re.I)
    ctx = blob[max(0,m.start()-190): m.end()+190].replace("\n"," ") if m else blob[:380]
    out.append(f"[{r['component']}] {rid} {r['case_id']} {r['source_stratum']}\n  MARKER: {mk}\n  CTX: ...{ctx}...\n")
Path(r"C:/Users/fengq/WorkBuddy/2026-09-06-21-48-32/adjud_dump.txt").write_text("\n".join(out), encoding="utf8")
print("items:", len(out))
