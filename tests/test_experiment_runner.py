from __future__ import annotations

import json
from pathlib import Path

from llm_personality_experiment.config import ExperimentConfig
from llm_personality_experiment.experiment.runner import ExperimentRunner


class _StubBackend:
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        return '{"submission":{"answers":[{"question_id":"q1","answer":"5"},{"question_id":"q2","answer":"6"},{"question_id":"q3","answer":"9"}],"feedback":"Great work, keep practicing and check carefully."}}'


def test_experiment_runner_writes_artifacts(config, monkeypatch, tmp_path) -> None:
    config_payload = config.model_dump(mode="python")
    config_payload["iterations"] = 2
    config_payload["paths"]["output_root"] = str(tmp_path / "artifacts")
    config_payload["analysis"]["generate_after_run"] = True
    runtime_config = ExperimentConfig.model_validate(config_payload)

    monkeypatch.setattr("llm_personality_experiment.experiment.runner.create_backend", lambda _: _StubBackend())

    run_paths = ExperimentRunner(runtime_config).run()

    assert Path(run_paths.log_path).exists()
    assert Path(run_paths.tasks_path).exists()
    assert Path(run_paths.metadata_path).exists()
    assert Path(run_paths.summary_path).exists()
    assert (Path(run_paths.analysis_dir) / "metrics_over_time.png").exists()
    assert (Path(run_paths.analysis_dir) / "selection_counts.png").exists()
    assert (Path(run_paths.analysis_dir) / "agent_failure_counts.png").exists()
    assert (Path(run_paths.analysis_dir) / "failure_type_heatmap.png").exists()

    run_metadata = json.loads(Path(run_paths.metadata_path).read_text(encoding="utf-8"))
    assert run_metadata["backend"]["model_name"] == "test-model"
    assert run_metadata["selection"]["agents_per_task"] == 2

    log_lines = Path(run_paths.log_path).read_text(encoding="utf-8").splitlines()
    task_lines = Path(run_paths.tasks_path).read_text(encoding="utf-8").splitlines()
    assert len(log_lines) == 2
    assert len(task_lines) == 2

    first_record = json.loads(log_lines[0])
    assert first_record["run_metadata"]["backend"]["model_name"] == "test-model"
    assert first_record["iteration"] == 1
    assert len(first_record["agent_attempts"]) == 2
    assert first_record["selection"]["selected_agents"]

    summary = json.loads(Path(run_paths.summary_path).read_text(encoding="utf-8"))
    assert summary["run_metadata"]["backend"]["model_name"] == "test-model"
    assert summary["total_tasks"] == 2
    assert summary["total_attempts"] == 4
