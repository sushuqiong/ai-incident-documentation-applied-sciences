from __future__ import annotations

import copy


def apply_event_log(payload: dict) -> dict:
    """Replay the synthetic append-only event log into a recoverable current state."""
    state = copy.deepcopy(payload)
    history = []
    for event in state.get("status_events", []):
        history.append(copy.deepcopy(event))
        target = event["target_id"]
        if event["event_type"] == "relation_withdrawn":
            for relation in state["relations"]:
                if relation["relation_id"] == target:
                    relation["status"] = "withdrawn"
                    relation["withdrawal_event_id"] = event["event_id"]
        elif event["event_type"] == "source_invalidated":
            for source in state["sources"]:
                if source["source_id"] == target:
                    source["status"] = "invalidated"
        elif event["event_type"] == "administrative_closed":
            for assertion in state["assertions"]:
                if assertion["assertion_id"] == target:
                    assertion["administrative_state"] = "closed"
                    assertion["evidence_status"] = event.get("evidence_status", "unknown")
        elif event["event_type"] == "reopened":
            for assertion in state["assertions"]:
                if assertion["assertion_id"] == target:
                    assertion["administrative_state"] = "open"
    state["event_history"] = history
    return state
