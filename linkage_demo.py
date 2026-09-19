from __future__ import annotations

import json
from pathlib import Path

from candidate_assertion import apply_candidate_assertions
from versioned_event_log import apply_event_log


HERE = Path(__file__).resolve().parent


def run() -> dict:
    payload = json.loads((HERE / "synthetic_event_log_input.json").read_text(encoding="utf-8"))
    return {
        "candidate_assertions": apply_candidate_assertions(payload),
        "versioned_event_log": apply_event_log(payload),
        "interpretation": (
            "Both versioned structures provided the tested representational capability under the synthetic "
            "operations. This output is not a benchmark of accuracy, efficiency, or governance effect."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
