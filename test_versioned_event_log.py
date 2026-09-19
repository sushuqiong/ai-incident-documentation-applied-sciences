import json
import unittest
from pathlib import Path

from candidate_assertion import apply_candidate_assertions
from versioned_event_log import apply_event_log


class SyntheticStructureTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).parent / "synthetic_event_log_input.json"
        self.payload = json.loads(path.read_text(encoding="utf-8"))
        self.candidate = apply_candidate_assertions(self.payload)
        self.event_log = apply_event_log(self.payload)

    def test_source_and_assertion_addition_are_retained(self):
        for result in [self.candidate, self.event_log]:
            self.assertEqual(len(result["sources"]), 2)
            self.assertEqual(len(result["assertions"]), 2)

    def test_conflicting_assertions_coexist(self):
        for result in [self.candidate, self.event_log]:
            self.assertEqual({item["status"] for item in result["assertions"]}, {"active", "disputed"})

    def test_all_relation_types_are_represented(self):
        expected = {"same_incident", "related_incident", "same_deployment"}
        for result in [self.candidate, self.event_log]:
            self.assertEqual({item["relation_type"] for item in result["relations"]}, expected)

    def test_relation_withdrawal_is_traceable(self):
        for result in [self.candidate, self.event_log]:
            relation = next(item for item in result["relations"] if item["relation_id"] == "R1")
            self.assertEqual(relation["status"], "withdrawn")
            self.assertEqual(relation["withdrawal_event_id"], "E0")

    def test_source_invalidation_is_represented(self):
        for result in [self.candidate, self.event_log]:
            source = next(item for item in result["sources"] if item["source_id"] == "S2")
            self.assertEqual(source["status"], "invalidated")

    def test_closure_evidence_state_and_reopening_are_separate(self):
        for result in [self.candidate, self.event_log]:
            assertion = next(item for item in result["assertions"] if item["assertion_id"] == "A1")
            self.assertEqual(assertion["administrative_state"], "open")
            self.assertEqual(assertion["evidence_status"], "insufficient")

    def test_histories_are_retained(self):
        self.assertEqual(len(self.event_log["event_history"]), 4)
        history = self.candidate["candidate_history"]
        self.assertEqual(sum(len(items) for items in history.values()), 4)

    def test_provenance_trace_is_recoverable(self):
        for result in [self.candidate, self.event_log]:
            source_ids = {item["source_id"] for item in result["sources"]}
            self.assertTrue(all(item["source_id"] in source_ids for item in result["assertions"]))


if __name__ == "__main__":
    unittest.main()
