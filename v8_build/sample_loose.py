# -*- coding: utf-8 -*-
"""Random sample (fixed seed) from the loosely-specified probes, for adjudication."""
import csv, re, random
from pathlib import Path
csv.field_size_limit(10**9)
SUP = Path(__file__).resolve().parent.parent / "02_supplement"
reg = {r["record_id"]: r for r in csv.DictReader(open(SUP/"source_registry.csv", encoding="utf-8-sig"))}
red = list(csv.DictReader(open(SUP/"independent_mechanical_redecode_v8.csv", encoding="utf-8-sig")))
COLS = ['source_excerpt','evidence_excerpt_v25','reverification_excerpt',
        'v29_exposure_denominator_present_evidence_excerpt',
        'v29_follow_up_window_present_evidence_excerpt',
        'v29_closure_basis_present_evidence_excerpt']
LOOSE = {"date","evidence_basis","uncertainty","trace_coverage","time_origin","owner",
         "exposure_qualified_observation"}
cand = [r for r in red if r["mechanical_probe_fired"]=="yes" and r["semantic_status"]=="not_recovered"
        and r["component"] in LOOSE]
random.seed(20260924)
by = {}
for r in cand: by.setdefault(r["component"], []).append(r)
sample = []
for comp, lst in sorted(by.items()):
    k = min(2, len(lst))
    sample += random.sample(lst, k)
out=[]
for r in sample:
    blob = " ~ ".join((reg[r["record_id"]].get(c) or "") for c in COLS)
    mk = r["matched_markers"].split(" | ")[0]
    m = re.search(re.escape(mk), blob, re.I)
    ctx = blob[max(0,m.start()-190): m.end()+190].replace("\n"," ") if m else blob[:380]
    out.append(f"[{r['component']}] {r['record_id']} {r['case_id']} {r['source_stratum']}\n  MARKER: {mk}\n  CTX: ...{ctx}...\n")
Path(r"C:/Users/fengq/WorkBuddy/2026-09-06-21-48-32/adjud_loose.txt").write_text("\n".join(out), encoding="utf8")
print("pool:", len(cand), "| sample:", len(sample))
print("pool by component:", {k: len(v) for k, v in sorted(by.items())})
