from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from candidate_assertion import apply_candidate_assertions
from versioned_event_log import apply_event_log

HERE = Path(__file__).resolve().parent
STATES = {"complete_support", "partial_support", "not_recovered", "unclear", "not_applicable"}


def rows(name):
    return [json.loads(line) for line in (HERE / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    components = rows("component_labels_v6_1400.jsonl")
    fields = rows("field_states_v6_300.jsonl")
    stats = json.loads((HERE / "statistics_v6.json").read_text(encoding="utf-8"))
    assert len(components) == len({(r["record_id"], r["field"], r["component"]) for r in components}) == 1400
    assert len(fields) == len({(r["record_id"], r["field"]) for r in fields}) == 300
    assert len({r["record_id"] for r in fields}) == 100
    assert len({r["canonical_cluster_id"] for r in fields}) == 91
    assert {r["canonical_cluster_id"] for r in fields} == {f"CL{i:03d}" for i in range(1, 92)}
    assert sum(r["primary_support_status"] == "supported_by_retained_evidence" for r in components) == 215
    assert sum(r["boundary_support_status"] == "supported_by_retained_evidence" for r in components) == 228
    assert all(r["primary_state"] in STATES and r["boundary_state"] in STATES for r in fields)
    for field in ("exposure", "follow_up", "closure"):
        assert sum(item["count"] for item in stats["primary_fields"][field]["states"].values()) == 100
    payload = json.loads((HERE / "synthetic_event_log_input.json").read_text(encoding="utf-8"))
    expected = json.loads((HERE / "synthetic_expected_outputs.json").read_text(encoding="utf-8"))
    assert apply_candidate_assertions(payload) == expected["candidate_assertions"]
    assert apply_event_log(payload) == expected["versioned_event_log"]
    result = subprocess.run([sys.executable, "-m", "unittest", "-q", "test_versioned_event_log.py"], cwd=HERE, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    manifest = rows("public_release_manifest.jsonl")
    for item in manifest:
        path = HERE / item["path"]
        assert path.is_file() and path.stat().st_size == item["size"] and digest(path) == item["sha256"]
    print("v6_release_verification_passed")


if __name__ == "__main__":
    main()
