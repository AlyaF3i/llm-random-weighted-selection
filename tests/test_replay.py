from __future__ import annotations

import json

from llm_personality_experiment.analysis.replay import (
    _aggregate_weights,
    _normalize_selected_names,
    load_replay_frames,
)


def test_load_replay_frames_reads_task_level_records(tmp_path) -> None:
    log_path = tmp_path / "experiment.jsonl"
    record = {
        "iteration": 3,
        "task": {
            "task_id": "exam-00003-addition",
            "questions": [{"prompt": "What is 1 + 2?", "question_id": "q1"}],
        },
        "selection": {"selected_agents": ["always_correct__01", "sometimes_correct__01"]},
        "weights_before": {"always_correct__01": 0.6, "sometimes_correct__01": 0.5},
        "weights_after": {"always_correct__01": 0.7, "sometimes_correct__01": 0.4},
        "agent_attempts": [
            {"agent_name": "always_correct__01", "verification": {"correctness_score": 1.0, "json_valid": True}, "had_failure": False},
            {"agent_name": "sometimes_correct__01", "verification": {"correctness_score": 0.0, "json_valid": True}, "had_failure": False},
        ],
    }
    log_path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    frames = load_replay_frames(log_path)

    assert len(frames) == 1
    assert frames[0].iteration == 3
    assert frames[0].task_id == "exam-00003-addition"
    assert frames[0].question_prompt == "What is 1 + 2?"
    assert frames[0].selected_agents == ("always_correct__01", "sometimes_correct__01")


def test_replay_family_helpers_group_duplicate_agents() -> None:
    weights = {
        "always_correct__01": 0.8,
        "always_correct__02": 0.6,
        "always_nice_teacher__01": 0.4,
    }

    aggregated = _aggregate_weights(weights, family_view=True)
    selected = _normalize_selected_names(("always_correct__01", "always_correct__02"), family_view=True)

    assert aggregated == {
        "always_correct": 0.7,
        "always_nice_teacher": 0.4,
    }
    assert selected == ("always_correct",)
