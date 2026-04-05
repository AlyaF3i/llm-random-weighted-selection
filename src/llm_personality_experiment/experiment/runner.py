"""End-to-end experiment runner."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from llm_personality_experiment.agents.backend import create_backend
from llm_personality_experiment.agents.client import AgentRunner
from llm_personality_experiment.agents.models import AgentState
from llm_personality_experiment.agents.personality import load_personalities
from llm_personality_experiment.analysis.plots import generate_plots
from llm_personality_experiment.analysis.summary import write_summary
from llm_personality_experiment.config import ExperimentConfig, dump_config
from llm_personality_experiment.experiment.models import RunPaths
from llm_personality_experiment.logging_utils.jsonl_logger import JSONLExperimentLogger
from llm_personality_experiment.scoring.models import AgentMetrics
from llm_personality_experiment.scoring.normalization import normalize_observation
from llm_personality_experiment.scoring.scoring import compute_raw_scores
from llm_personality_experiment.scoring.selection import compute_weights_by_agent, select_agents
from llm_personality_experiment.scoring.updates import update_metrics
from llm_personality_experiment.tasks.generator import TaskGenerator
from llm_personality_experiment.tasks.solver import solve_task
from llm_personality_experiment.tasks.verifier import parse_and_verify_output
from llm_personality_experiment.utils.io import ensure_directory, write_json
from llm_personality_experiment.utils.seed import create_rng


class ExperimentRunner:
    """Coordinate generation, selection, model execution, scoring, and logging."""

    def __init__(self, config: ExperimentConfig) -> None:
        self._config = config
        self._task_generator = TaskGenerator(config)
        self._selection_rng = create_rng(config.seed + 104_729)
        self._backend = create_backend(config.backend)
        self._agent_runner = AgentRunner(self._backend)

    def run(self) -> RunPaths:
        """Execute the configured experiment and return output paths."""

        run_paths = self._create_run_paths()
        dump_config(self._config, run_paths.config_snapshot_path)
        logger = JSONLExperimentLogger(run_paths.log_path)
        agents = self._create_agents()
        run_metadata = self._build_run_metadata(run_id=Path(run_paths.run_dir).name, agents=agents)
        write_json(run_paths.metadata_path, run_metadata)
        attempt_id = 0

        for iteration in range(1, self._config.iterations + 1):
            task = self._task_generator.generate(iteration)
            solver_result = solve_task(task)
            weights_before = compute_weights_by_agent(agents, self._config.selection.metric_weights)
            all_metrics_before = {agent.name: agent.metrics.to_dict() for agent in agents}
            selection_outcome = select_agents(
                agents=agents,
                metric_weights=self._config.selection.metric_weights,
                epsilon=self._config.selection.epsilon,
                agents_per_task=self._config.selection.agents_per_task,
                rng=self._selection_rng,
            )
            selected_agents = [
                next(agent for agent in agents if agent.name == selected_agent_name)
                for selected_agent_name in selection_outcome.selected_agents
            ]

            for selected_agent in selected_agents:
                attempt_id += 1
                metrics_before = selected_agent.metrics
                backend_error: str | None = None

                try:
                    raw_output = self._agent_runner.run(selected_agent.personality, task)
                except Exception as exc:  # pragma: no cover - exercised in real backend runs
                    raw_output = ""
                    backend_error = str(exc)

                verification_result = parse_and_verify_output(
                    raw_output=raw_output,
                    task=task,
                    solution=solver_result,
                    evaluation_config=self._config.evaluation,
                )
                raw_scores = compute_raw_scores(solver_result, verification_result)
                normalized_scores = normalize_observation(raw_scores)
                metrics_after = update_metrics(
                    current=metrics_before,
                    observation=normalized_scores,
                    defaults=self._config.metrics,
                    rules=self._config.updates,
                )
                selected_agent.metrics = metrics_after
                selected_agent.interactions += 1

                weights_after = compute_weights_by_agent(agents, self._config.selection.metric_weights)
                all_metrics_after = {agent.name: agent.metrics.to_dict() for agent in agents}

                logger.log(
                    {
                        "attempt_id": attempt_id,
                        "iteration": iteration,
                        "run_metadata": run_metadata,
                        "task": task.to_dict(),
                        "agent": selected_agent.to_dict(),
                        "solver": solver_result.to_dict(),
                        "raw_output": raw_output,
                        "backend_error": backend_error,
                        "verification": verification_result.to_dict(),
                        "raw_scores": raw_scores.to_dict(),
                        "normalized_scores": normalized_scores.to_dict(),
                        "metrics_before": metrics_before.to_dict(),
                        "metrics_after": metrics_after.to_dict(),
                        "all_agents_metrics_before": all_metrics_before,
                        "all_agents_metrics_after": all_metrics_after,
                        "weights_before": weights_before,
                        "weights_after": weights_after,
                        "selection": selection_outcome.to_dict(),
                    }
                )

        write_summary(
            log_path=run_paths.log_path,
            output_path=run_paths.summary_path,
            aggregate_every=self._config.analysis.aggregate_every,
            run_metadata=run_metadata,
        )
        if self._config.analysis.generate_after_run:
            generate_plots(log_path=run_paths.log_path, output_dir=run_paths.analysis_dir)
        return run_paths

    def _build_run_metadata(self, run_id: str, agents: list[AgentState]) -> dict[str, object]:
        return {
            "run_id": run_id,
            "created_at_utc": run_id,
            "backend": self._config.backend.model_dump(mode="json"),
            "selection": self._config.selection.model_dump(mode="json"),
            "metrics": self._config.metrics.model_dump(mode="json"),
            "updates": self._config.updates.model_dump(mode="json"),
            "task_generation": self._config.task_generation.model_dump(mode="json"),
            "evaluation": self._config.evaluation.model_dump(mode="json"),
            "scenario_mix": dict(self._config.scenario_mix),
            "personalities": {
                "dir": self._config.personalities_dir,
                "duplication": dict(self._config.personalities.duplication),
                "loaded_agent_names": [agent.name for agent in agents],
                "loaded_personalities": sorted({agent.personality.name for agent in agents}),
                "total_agents": len(agents),
            },
            "config": self._config.model_dump(mode="json"),
        }

    def _create_agents(self) -> list[AgentState]:
        personalities = load_personalities(self._config.personalities_dir)
        initial_metrics = AgentMetrics.from_dict(self._config.metrics.initial)
        agents: list[AgentState] = []
        for personality in personalities:
            copy_count = self._config.personalities.duplication.get(personality.name, 1)
            for index in range(copy_count):
                if copy_count == 1:
                    agent_name = personality.name
                else:
                    agent_name = f"{personality.name}__{index + 1:02d}"
                agents.append(AgentState(name=agent_name, personality=personality, metrics=initial_metrics))
        if not agents:
            raise ValueError("No agents were created; check personalities and duplication settings")
        return agents

    def _create_run_paths(self) -> RunPaths:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_root = ensure_directory(self._config.paths.output_root)
        run_dir = ensure_directory(Path(output_root) / self._config.paths.runs_dirname / timestamp)
        analysis_dir = ensure_directory(run_dir / self._config.paths.analysis_dirname)
        return RunPaths(
            run_dir=str(run_dir),
            log_path=str(run_dir / self._config.paths.logs_filename),
            analysis_dir=str(analysis_dir),
            metadata_path=str(run_dir / self._config.paths.metadata_filename),
            summary_path=str(run_dir / self._config.paths.summary_filename),
            config_snapshot_path=str(run_dir / self._config.paths.config_snapshot_filename),
        )
