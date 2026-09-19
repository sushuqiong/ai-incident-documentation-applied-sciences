from __future__ import annotations

import copy


def apply_candidate_assertions(payload: dict) -> dict:
    """Apply synthetic status events while retaining per-entity assertion histories."""
    state = copy.deepcopy(payload)
    source_history = []
    assertion_history = []
    relation_history = []

    for event in state.get("status_events", []):
        target = event["target_id"]
        event_type = event["event_type"]
        if event_type == "relation_withdrawn":
            for relation in state["relations"]:
                if relation["relation_id"] == target:
                    relation_history.append({"before": copy.deepcopy(relation), "event": copy.deepcopy(event)})
                    relation["status"] = "withdrawn"
                    relation["withdrawal_event_id"] = event["event_id"]
                    relation_history[-1]["after"] = copy.deepcopy(relation)
        elif event_type == "source_invalidated":
            for source in state["sources"]:
                if source["source_id"] == target:
                    source_history.append({"before": copy.deepcopy(source), "event": copy.deepcopy(event)})
                    source["status"] = "invalidated"
                    source_history[-1]["after"] = copy.deepcopy(source)
        elif event_type == "administrative_closed":
            for assertion in state["assertions"]:
                if assertion["assertion_id"] == target:
                    assertion_history.append({"before": copy.deepcopy(assertion), "event": copy.deepcopy(event)})
                    assertion["administrative_state"] = "closed"
                    assertion["evidence_status"] = event.get("evidence_status", "unknown")
                    assertion_history[-1]["after"] = copy.deepcopy(assertion)
        elif event_type == "reopened":
            for assertion in state["assertions"]:
                if assertion["assertion_id"] == target:
                    assertion_history.append({"before": copy.deepcopy(assertion), "event": copy.deepcopy(event)})
                    assertion["administrative_state"] = "open"
                    assertion_history[-1]["after"] = copy.deepcopy(assertion)

    state["candidate_history"] = {
        "sources": source_history,
        "assertions": assertion_history,
        "relations": relation_history,
    }
    return state
