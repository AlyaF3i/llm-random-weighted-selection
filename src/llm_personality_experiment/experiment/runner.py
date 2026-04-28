"""End-to-end experiment runner."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from llm_personality_experiment.agents.backend import create_backend
from llm_personality_experiment.agents.client import AgentRunner
from llm_personality_experiment.agents.models import AgentState
from llm_personality_experiment.agents.personality import load_personalities
from llm_personality_experiment.agents.sampling import load_sampling_profiles
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
from llm_personality_experiment.utils.io import append_jsonl, ensure_directory, write_json
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

        # START: RUN-LEVEL ARTIFACT SETUP
        run_paths = self._create_run_paths()
        dump_config(self._config, run_paths.config_snapshot_path)
        logger = JSONLExperimentLogger(run_paths.log_path)
        agents = self._create_agents()
        run_metadata = self._build_run_metadata(run_id=Path(run_paths.run_dir).name, agents=agents)
        write_json(run_paths.metadata_path, run_metadata)
        attempt_id = 0
        # END: RUN-LEVEL ARTIFACT SETUP

        # START: MAIN EXPERIMENT LOOP
        for iteration in range(1, self._config.iterations + 1):
            # START: TASK GENERATION AND DETERMINISTIC SOLVER BASELINE
            task = self._task_generator.generate(iteration)
            solver_result = solve_task(task)
            # END: TASK GENERATION AND DETERMINISTIC SOLVER BASELINE

            # START: AGENT STATE SNAPSHOT BEFORE SELECTION
            weights_before = compute_weights_by_agent(agents, self._config.selection.metric_weights)
            all_metrics_before = {agent.name: agent.metrics.to_dict() for agent in agents}
            # END: AGENT STATE SNAPSHOT BEFORE SELECTION

            # START: AGENT SELECTION FOR CURRENT TASK
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
            # END: AGENT SELECTION FOR CURRENT TASK

            # START: TASK-LEVEL RECORD BEFORE MODEL EXECUTION
            append_jsonl(
                run_paths.tasks_path,
                {
                    "iteration": iteration,
                    "run_metadata": run_metadata,
                    "task": task.to_dict(),
                    "solver": solver_result.to_dict(),
                    "selection": selection_outcome.to_dict(),
                },
            )
            # END: TASK-LEVEL RECORD BEFORE MODEL EXECUTION

            # START: SELECTED AGENT EXECUTION, EVALUATION, AND STAGED UPDATES
            agent_attempts: list[dict[str, object]] = []
            pending_updates: list[tuple[AgentState, AgentMetrics, AgentMetrics]] = []
            for selected_agent in selected_agents:
                # START: SINGLE AGENT ATTEMPT
                attempt_id += 1
                metrics_before = selected_agent.metrics
                backend_error: str | None = None

                # START: MODEL GENERATION CALL
                try:
                    raw_output = self._agent_runner.run(selected_agent.personality, task)
                except Exception as exc:  # pragma: no cover - exercised in real backend runs
                    raw_output = ""
                    backend_error = str(exc)
                # END: MODEL GENERATION CALL

                # START: DETERMINISTIC VERIFICATION AND SCORE COMPUTATION
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
                # END: DETERMINISTIC VERIFICATION AND SCORE COMPUTATION

                # START: STAGE METRIC UPDATES UNTIL ALL SELECTED AGENTS FINISH
                pending_updates.append((selected_agent, metrics_before, metrics_after))
                agent_attempts.append(
                    {
                        "attempt_id": attempt_id,
                        "agent_name": selected_agent.name,
                        "personality": selected_agent.personality.to_dict(),
                        "interactions_before": selected_agent.interactions,
                        "interactions_after": selected_agent.interactions + 1,
                        "metrics_before": metrics_before.to_dict(),
                        "metrics_after": metrics_after.to_dict(),
                        "raw_output": raw_output,
                        "backend_error": backend_error,
                        "verification": verification_result.to_dict(),
                        "raw_scores": raw_scores.to_dict(),
                        "normalized_scores": normalized_scores.to_dict(),
                        "had_failure": bool(backend_error) or bool(verification_result.failure_types),
                    }
                )
                # END: STAGE METRIC UPDATES UNTIL ALL SELECTED AGENTS FINISH
                # END: SINGLE AGENT ATTEMPT
            # END: SELECTED AGENT EXECUTION, EVALUATION, AND STAGED UPDATES

            # START: APPLY STAGED METRIC UPDATES AFTER ALL SELECTED AGENTS FINISH
            for selected_agent, _, metrics_after in pending_updates:
                selected_agent.metrics = metrics_after
                selected_agent.interactions += 1
            # END: APPLY STAGED METRIC UPDATES AFTER ALL SELECTED AGENTS FINISH

            # START: AGENT STATE SNAPSHOT AFTER EVALUATION
            weights_after = compute_weights_by_agent(agents, self._config.selection.metric_weights)
            all_metrics_after = {agent.name: agent.metrics.to_dict() for agent in agents}
            # END: AGENT STATE SNAPSHOT AFTER EVALUATION

            # START: ITERATION LOGGING WITH BEFORE AND AFTER STATES
            logger.log(
                {
                    "iteration": iteration,
                    "run_metadata": run_metadata,
                    "task": task.to_dict(),
                    "solver": solver_result.to_dict(),
                    "selection": selection_outcome.to_dict(),
                    "all_agents_metrics_before": all_metrics_before,
                    "all_agents_metrics_after": all_metrics_after,
                    "weights_before": weights_before,
                    "weights_after": weights_after,
                    "agent_attempts": agent_attempts,
                }
            )
            # END: ITERATION LOGGING WITH BEFORE AND AFTER STATES
        # END: MAIN EXPERIMENT LOOP

        # START: POST-RUN SUMMARY AND PLOT GENERATION
        write_summary(
            log_path=run_paths.log_path,
            output_path=run_paths.summary_path,
            aggregate_every=self._config.analysis.aggregate_every,
            run_metadata=run_metadata,
        )
        if self._config.analysis.generate_after_run:
            generate_plots(log_path=run_paths.log_path, output_dir=run_paths.analysis_dir)
        # END: POST-RUN SUMMARY AND PLOT GENERATION
        return run_paths

    def _build_run_metadata(self, run_id: str, agents: list[AgentState]) -> dict[str, object]:
        return {
            "experiment_name": self._config.experiment_name,
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
                "sampling_parameters_path": self._config.personalities.sampling_parameters_path,
                "sampling_profiles": {
                    agent.personality.name: agent.personality.sampling_parameters.model_dump(mode="json")
                    for agent in agents
                },
                "loaded_agent_names": [agent.name for agent in agents],
                "loaded_personalities": sorted({agent.personality.name for agent in agents}),
                "total_agents": len(agents),
            },
            "config": self._config.model_dump(mode="json"),
        }

    def _create_agents(self) -> list[AgentState]:
        # START: PERSONALITY LOADING AND AGENT DUPLICATION
        personalities_dir = Path(self._config.personalities_dir)
        personality_names = sorted(path.stem for path in personalities_dir.glob("*.md"))
        sampling_profiles = load_sampling_profiles(
            path=self._config.personalities.sampling_parameters_path,
            personality_names=personality_names,
            backend_config=self._config.backend,
        )
        personalities = load_personalities(personalities_dir, sampling_profiles=sampling_profiles)
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
        # END: PERSONALITY LOADING AND AGENT DUPLICATION
        return agents

    def _create_run_paths(self) -> RunPaths:
        # START: RUN DIRECTORY NAMING AND OUTPUT PATH RESOLUTION
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_root = ensure_directory(self._config.paths.output_root)
        run_name = f"{self._slugify_name(self._config.experiment_name)}_{timestamp}"
        run_dir = ensure_directory(Path(output_root) / self._config.paths.runs_dirname / run_name)
        analysis_dir = ensure_directory(run_dir / self._config.paths.analysis_dirname)
        paths = RunPaths(
            run_dir=str(run_dir),
            log_path=str(run_dir / self._config.paths.logs_filename),
            tasks_path=str(run_dir / self._config.paths.tasks_filename),
            analysis_dir=str(analysis_dir),
            metadata_path=str(run_dir / self._config.paths.metadata_filename),
            summary_path=str(run_dir / self._config.paths.summary_filename),
            config_snapshot_path=str(run_dir / self._config.paths.config_snapshot_filename),
        )
        # END: RUN DIRECTORY NAMING AND OUTPUT PATH RESOLUTION
        return paths

    def _slugify_name(self, value: str) -> str:
        cleaned = "".join(character.lower() if character.isalnum() else "_" for character in value.strip())
        collapsed = "_".join(part for part in cleaned.split("_") if part)
        return collapsed or "experiment"
