# -*- coding: utf-8 -*-
"""Draw a simple random sample from the blinded coding sheet for agent recoding.

The sealed key is NOT read here. The sample is drawn uniformly from all 1,400 items so
that the resulting agreement rate is an unbiased estimate for the full decision set
(no stratification, no oversampling of any status).
"""
import csv, random, sys
from pathlib import Path
csv.field_size_limit(10**9)
PKG = Path(__file__).resolve().parent.parent / "02_supplement" / "blinded_review_package_v8"
rows = list(csv.DictReader(open(PKG/"blinded_coding_sheet_v8.csv", encoding="utf-8-sig")))
random.seed(20260924)
N = int(sys.argv[1]) if len(sys.argv) > 1 else 120
batch = int(sys.argv[2]) if len(sys.argv) > 2 else 1
NB = 4
sample = random.sample(rows, N)
per = (N + NB - 1) // NB
part = sample[(batch-1)*per: batch*per]
TRUNC = 1500
out = []
for i, r in enumerate(part, 1):
    txt = (r["retained_text_to_review"] or "")
    trunc = len(txt) > TRUNC
    out.append(f"#{r['item_id']} [{r['field']}/{r['component']}] (text{' TRUNCATED' if trunc else ''})\n"
               f"  DEF: {r['component_definition']}\n"
               f"  TXT: {txt[:TRUNC]}")
Path(r"C:/Users/fengq/WorkBuddy/2026-09-06-21-48-32/blind_batch.txt").write_text("\n".join(out), encoding="utf8")
print(f"sample N={N}; batch {batch}: {len(part)} items; written blind_batch.txt")
print("item_ids:", [r['item_id'] for r in part])
