# -*- coding: utf-8 -*-
"""
Task-level capability tests T09-T11 (v8).

Reviewer point 5: T01-T08 show that two versioned structures can *represent* the
tested operations. They do not show that either structure supports a task a
record keeper would actually perform. The reviewer named three:

  T09  after a source is invalidated, find every affected judgement;
  T10  restore the state of the record as it stood at a past time point;
  T11  state which evidence components a closure decision is missing.

Each test below uses the SAME frozen synthetic input as T01-T08
(`synthetic_event_log_input_v7.json`). Expected answers and pass conditions were
fixed before the tests were written, and are stored in
`synthetic_task_expected_outputs_v8.json`.

What these tests do and do not show:
  - They show that the frozen payload, under a specified traversal rule, yields
    the specified answer.
  - They do not measure accuracy, query completeness against a real corpus,
    computation time, storage cost, or maintenance burden. No comparison with
    an existing system is made or implied.

Run:  python test_synthetic_task_capability_v8.py
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
V7SUP = Path(r"C:/Users/fengq/Desktop/AI健康医学_Applied_Sciences_v7_20260920_175106/02_supplement")
OUT = HERE.parent / "02_supplement"

CLOSURE_COMPONENTS = {"scope", "evidence_basis", "date", "owner", "uncertainty", "reopening_rule"}


def load_payload() -> dict:
    return json.loads((V7SUP / "synthetic_event_log_input_v7.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# T09 - downstream impact of a source invalidation
#
# Rule (fixed in advance): an assertion is affected if
#   (i)   it is sourced from the invalidated source, or
#   (ii)  it is linked to an affected assertion by a relation
#         (either direction) or by a disputed_by / supersedes reference, or
#   (iii) it is used as the basis of a status event whose target is affected.
# Sources derived FROM the invalidated source are affected transitively.
# ---------------------------------------------------------------------------
def affected_after_source_invalidation(payload: dict, source_id: str) -> dict:
    bad_sources = {source_id}
    changed = True
    while changed:                      # transitive: sources derived from a bad source
        changed = False
        for s in payload["sources"]:
            if s["source_id"] not in bad_sources and any(
                    p in bad_sources for p in s.get("was_derived_from", [])):
                bad_sources.add(s["source_id"])
                changed = True

    assertions = payload["assertions"]
    affected = {a["assertion_id"] for a in assertions if a["source_id"] in bad_sources}

    changed = True
    while changed:                      # propagate along relations and disputes
        changed = False
        for r in payload["relations"]:
            for x, y in ((r["from_id"], r["to_id"]), (r["to_id"], r["from_id"])):
                if x in affected and y not in affected:
                    affected.add(y)
                    changed = True
        for a in assertions:
            for other in list(a.get("disputed_by", [])) + list(a.get("supersedes", [])):
                if a["assertion_id"] in affected and other not in affected:
                    affected.add(other)
                    changed = True
                if other in affected and a["assertion_id"] not in affected:
                    affected.add(a["assertion_id"])
                    changed = True

    # status events whose basis assertions are affected keep their history but
    # must be reviewable: list them, do not delete them.
    affected_events = sorted(
        e["event_id"] for e in payload["status_events"]
        if any(b in affected for b in e.get("basis_assertion_ids", [])))

    return {"invalidated_sources": sorted(bad_sources),
            "affected_assertions": sorted(affected),
            "affected_status_events": affected_events}


# ---------------------------------------------------------------------------
# T10 - state as at a past time point
#
# Rule (fixed in advance): replay status_events in effective_time order up to
# and including the queried instant; later events are ignored; no event is
# deleted. Administrative state and evidence status are reported separately.
# ---------------------------------------------------------------------------
def state_at(payload: dict, assertion_id: str, instant: str) -> dict:
    states = {}
    for a in payload["assertions"]:
        if a["assertion_id"] == assertion_id:
            states["administrative_state"] = a.get("administrative_state", "open")
            states["evidence_status"] = a.get("evidence_status", "unresolved")
    for e in sorted(payload["status_events"], key=lambda e: e["effective_time"]):
        if e["effective_time"] > instant:
            continue
        if e["target_id"] != assertion_id:
            continue
        t = e["event_type"]
        if t == "administrative_closed":
            states["administrative_state"] = "closed"
            if e.get("evidence_status"):
                states["evidence_status"] = e["evidence_status"]
        elif t == "reopened":
            states["administrative_state"] = "open"
    states["as_at"] = instant
    return states


# ---------------------------------------------------------------------------
# T11 - evidence gap in a closure decision
#
# Rule (fixed in advance): a closure decision is supported only by assertions
# whose field is "closure" and whose status is "active". Report the closure
# components covered and the ones missing.
# ---------------------------------------------------------------------------
def closure_evidence_gap(payload: dict, assertion_id: str) -> dict:
    covered = {a["component"] for a in payload["assertions"]
               if a["field"] == "closure" and a["status"] == "active"}
    missing = sorted(CLOSURE_COMPONENTS - covered)
    return {"closure_components_required": sorted(CLOSURE_COMPONENTS),
            "covered_by_active_assertions": sorted(covered & CLOSURE_COMPONENTS),
            "missing_components": missing,
            "missing_count": len(missing)}


class TaskCapabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = load_payload()
        cls.expected = json.loads((HERE / "synthetic_task_expected_outputs_v8.json").read_text(encoding="utf-8"))

    def test_T09_source_invalidation_impact(self):
        got = affected_after_source_invalidation(self.payload, "S2")
        self.assertEqual(got, self.expected["T09"])
        # history must survive: the invalidation event is still present
        self.assertTrue(any(e["event_type"] == "source_invalidated" for e in self.payload["status_events"]))

    def test_T10_historical_state_restoration(self):
        for probe in self.expected["T10_probes"]:
            got = state_at(self.payload, probe["assertion_id"], probe["instant"])
            want = dict(probe["expected"])
            self.assertEqual(got, want, msg=f"failed at {probe['instant']}")

    def test_T11_closure_evidence_gap(self):
        got = closure_evidence_gap(self.payload, "A1")
        self.assertEqual(got, self.expected["T11"])

    def test_T10_replay_does_not_mutate_payload(self):
        before = json.dumps(self.payload, sort_keys=True)
        state_at(self.payload, "A1", "2026-01-04T12:00:00Z")
        self.assertEqual(json.dumps(self.payload, sort_keys=True), before)


# Expected answers, fixed before the tests were written.
#
# Correction note: T09's affected_status_events was first written as ["E1","E3"].
# That was a mis-derivation by hand. Under the rule fixed in advance, E0 (basis
# A1,A2), E1 (basis A2), E2 (basis A1) and E3 (basis A2) all reference an
# affected assertion, so all four are affected. The expected list was corrected
# to ["E0","E1","E2","E3"]; the rule, the input and the traversal were not
# changed. Recorded here rather than silently.
EXPECTED = {
    "T09": {
        "invalidated_sources": ["S2"],
        "affected_assertions": ["A1", "A2"],
        "affected_status_events": ["E0", "E1", "E2", "E3"],
    },
    "T09_derivation_note": ("S2 invalidated -> A2 is sourced from S2 -> affected. A2 is linked to "
                            "A1 by disputed_by and by relations R1-R3 -> A1 affected. Every status "
                            "event lists A1 or A2 in basis_assertion_ids, so all four events are "
                            "flagged for review while none is deleted."),
    "T10_probes": [
        {"assertion_id": "A1", "instant": "2026-01-01T00:00:00Z",
         "expected": {"administrative_state": "open", "evidence_status": "unresolved",
                      "as_at": "2026-01-01T00:00:00Z"}},
        {"assertion_id": "A1", "instant": "2026-01-04T12:00:00Z",
         "expected": {"administrative_state": "closed", "evidence_status": "insufficient",
                      "as_at": "2026-01-04T12:00:00Z"}},
        {"assertion_id": "A1", "instant": "2026-01-05T12:00:00Z",
         "expected": {"administrative_state": "open", "evidence_status": "insufficient",
                      "as_at": "2026-01-05T12:00:00Z"}},
    ],
    "T11": {
        "closure_components_required": ["date", "evidence_basis", "owner", "reopening_rule",
                                        "scope", "uncertainty"],
        "covered_by_active_assertions": ["evidence_basis"],
        "missing_components": ["date", "owner", "reopening_rule", "scope", "uncertainty"],
        "missing_count": 5,
    },
}


def main() -> int:
    (HERE / "synthetic_task_expected_outputs_v8.json").write_text(
        json.dumps(EXPECTED, indent=1), encoding="utf-8")

    results = {}
    payload = load_payload()
    results["T09_source_invalidation_impact"] = affected_after_source_invalidation(payload, "S2")
    results["T10_historical_state_restoration"] = [
        state_at(payload, p["assertion_id"], p["instant"]) for p in EXPECTED["T10_probes"]]
    results["T11_closure_evidence_gap"] = closure_evidence_gap(payload, "A1")

    runner = unittest.TextTestRunner(verbosity=2)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TaskCapabilityTests)
    ok = runner.run(suite).wasSuccessful()

    results["all_passed"] = ok
    results["input"] = "synthetic_event_log_input_v7.json (frozen, unchanged)"
    results["scope_note"] = ("Representational capability on the frozen synthetic payload only. "
                             "No accuracy, completeness against a real corpus, timing, storage, "
                             "or comparison with an existing system is measured or implied.")
    (OUT / "synthetic_task_test_outputs_v8.json").write_text(
        json.dumps(results, indent=1), encoding="utf-8")

    print("\n--- actual outputs ---")
    print(json.dumps({k: v for k, v in results.items() if k != "scope_note"}, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
