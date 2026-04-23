# JSON Reference

This file explains the output files produced by each run of the math-exam experiment.

Main files in a run directory:

- `artifacts/runs/<run_id>/experiment.jsonl`
- `artifacts/runs/<run_id>/tasks.jsonl`
- `artifacts/runs/<run_id>/summary.json`
- `artifacts/runs/<run_id>/run_metadata.json`
- `artifacts/runs/<run_id>/config_snapshot.yaml`

## 1. `run_metadata.json`

This file is the fastest way to see which model and config were used for a run.

Top-level keys:

### `run_id`

- Type: string
- Meaning: full run folder name, built as `<experiment_name>_<timestamp>`.

### `experiment_name`

- Type: string
- Meaning: human-readable experiment label from the YAML config.

### `created_at_utc`

- Type: string
- Meaning: UTC timestamp component used inside `run_id`.

### `backend`

- Type: object
- Meaning: backend settings used for the run.

Keys include:

- `provider`
- `base_url`
- `model_name`
- `timeout_seconds`
- `temperature`
- `p_sample`
- `k_sample`

### `selection`

- Type: object
- Meaning: selection policy settings for the run.

Keys include:

- `epsilon`
- `agents_per_task`
- `metric_weights`

### `metrics`

- Type: object
- Meaning: metric defaults and baselines.

Keys include:

- `initial`
- `baseline`
- `min_value`
- `max_value`

### `updates`

- Type: object
- Meaning: baseline-aware update rates.

Keys include:

- `above_baseline`
- `below_baseline`

### `task_generation`

- Type: object
- Meaning: math-exam generation settings.

Keys include:

- `grade_label`
- `questions_per_exam_min`
- `questions_per_exam_max`
- `points_per_question`
- `operations`
- `mixed_operation_pool`

### `evaluation`

- Type: object
- Meaning: deterministic feedback-scoring configuration.

### `scenario_mix`

- Type: object
- Meaning: relative frequency for each exam scenario.

Keys:

- `addition`
- `subtraction`
- `multiplication`
- `mixed_review`

### `personalities`

- Type: object
- Meaning: loaded personality inventory for the run.

Keys include:

- `dir`
- `duplication`
- `sampling_parameters_path`
- `sampling_profiles`
- `loaded_agent_names`
- `loaded_personalities`
- `total_agents`

### `config`

- Type: object
- Meaning: full validated config dump used for the run.

## 2. `experiment.jsonl`

`experiment.jsonl` is the full replay log.

- It is JSONL, not one large JSON array.
- Each line is one JSON object.
- Each line is one task iteration.
- The selected agents for that task are stored inside `agent_attempts`.

Generated exams are stored here under the `task` key.

## Top-Level Keys In Each JSONL Record

### `iteration`

- Type: integer
- Meaning: task iteration number.

### `run_metadata`

- Type: object
- Meaning: embedded run-level metadata so each record is self-describing even if separated from the run folder.
- Same structure as `run_metadata.json`.

### `task`

- Type: object
- Meaning: exact generated math exam used for this iteration.

#### `task.task_id`

- Type: string
- Meaning: deterministic exam identifier.

#### `task.iteration`

- Type: integer
- Meaning: iteration number used to generate this exam.

#### `task.seed`

- Type: integer
- Meaning: deterministic seed recorded for this exam instance.

#### `task.scenario_type`

- Type: string
- Possible values:
  - `addition`
  - `subtraction`
  - `multiplication`
  - `mixed_review`
- Meaning: scenario label for the exam.

#### `task.grade_label`

- Type: string
- Meaning: human-readable difficulty label, for example `elementary school`.

#### `task.instructions`

- Type: string
- Meaning: instructions embedded into the task payload.

#### `task.questions`

- Type: array of objects
- Meaning: ordered list of exam questions.

Each question contains:

- `question_id`
- `prompt`
- `operation`
- `operands`
- `points`

#### `task.total_points`

- Type: integer
- Meaning: total available score on the exam.

### `solver`

- Type: object
- Meaning: deterministic answer-key output for the exam.

#### `solver.answer_key`

- Type: object
- Meaning: map from `question_id` to the correct final answer as a string.

#### `solver.total_points`

- Type: integer
- Meaning: total exam points.

#### `solver.question_count`

- Type: integer
- Meaning: total number of questions.

### `selection`

- Type: object
- Meaning: selection metadata for the task-level invitation event.

#### `selection.selected_agents`

- Type: array of strings
- Meaning: all agents selected for the task in that iteration.

#### `selection.explored`

- Type: boolean
- Meaning:
  - `true`: the selection used epsilon exploration
  - `false`: the selection used weighted sampling

#### `selection.probabilities`

- Type: object
- Meaning: normalized pre-selection probabilities for every available agent.

#### `selection.weights`

- Type: object
- Meaning: pre-selection weights for every available agent.

### `all_agents_metrics_before`

- Type: object
- Meaning: metric snapshot for every agent before the batch update for this task.

### `all_agents_metrics_after`

- Type: object
- Meaning: metric snapshot for every agent after all selected agents from this task were updated.

### `weights_before`

- Type: object
- Meaning: selection weight for every agent before the task.

### `weights_after`

- Type: object
- Meaning: selection weight for every agent after all selected agents from this task were updated.

### `agent_attempts`

- Type: array of objects
- Meaning: all invited-agent submissions for this iteration.

Each `agent_attempts[]` entry contains:

### `agent_attempts[].attempt_id`

- Type: integer
- Meaning: unique 1-based attempt counter across the run.

### `agent_attempts[].agent_name`

- Type: string
- Meaning: runtime agent name. Duplicated personalities are suffixed like `always_correct__01`.

### `agent_attempts[].personality`

- Type: object
- Meaning: personality metadata with:
  - `name`
  - `source_path`
  - `sampling_parameters`

### `agent_attempts[].personality.sampling_parameters`

- Type: object
- Meaning: the exact generation parameters used for that personality.

Keys:

- `temperature`
- `p_sample`
- `k_sample`

### `agent_attempts[].interactions_before`

- Type: integer
- Meaning: how many times this agent had been selected before this task.

### `agent_attempts[].interactions_after`

- Type: integer
- Meaning: how many times this agent had been selected after this task update.

### `agent_attempts[].metrics_before`

- Type: object
- Meaning: selected agent metrics before the update.

### `agent_attempts[].metrics_after`

- Type: object
- Meaning: selected agent metrics after the update.

Metric keys:

- `correctness`
- `completeness`
- `supportiveness`
- `reliability`

### `agent_attempts[].raw_output`

- Type: string
- Meaning: exact raw model text returned by the backend.

### `agent_attempts[].backend_error`

- Type: string or `null`
- Meaning: backend failure message if the model call failed.

### `agent_attempts[].verification`

- Type: object
- Meaning: strict parsing and deterministic grading result for `raw_output`.

Keys include:

- `json_valid`
- `schema_valid`
- `parsed_output`
- `answers`
- `feedback`
- `answered_count`
- `correct_count`
- `score_earned`
- `total_points`
- `correctness_score`
- `completeness_score`
- `supportiveness_score`
- `reliability`
- `failure_types`

Common `failure_types` values:

- `invalid_json`
- `schema_validation_failed`
- `duplicate_question_id`
- `unknown_question_id`
- `missing_feedback`

### `agent_attempts[].raw_scores`

- Type: object
- Meaning: direct metric observations before normalization.

### `agent_attempts[].normalized_scores`

- Type: object
- Meaning: normalized version of `raw_scores`.
- Current behavior: clamp each value to `[0, 1]`.

### `agent_attempts[].had_failure`

- Type: boolean
- Meaning: `true` if the backend failed or verification reported any failure type.

## 3. `tasks.jsonl`

`tasks.jsonl` is the task-only log.

- It stores one line per iteration.
- Each line includes:
  - `iteration`
  - `run_metadata`
  - `task`
  - `solver`
  - `selection`

Use this file when you want to inspect the exact questions asked without the full replay data.

## 4. `summary.json`

`summary.json` is the aggregate run summary.

Top-level keys:

### `run_metadata`

- Type: object
- Meaning: same run metadata described above, included for quick inspection of model and config settings.

### `total_tasks`

- Type: integer
- Meaning: number of task iterations in the run.

### `total_attempts`

- Type: integer
- Meaning: total number of invited-agent attempts across all tasks.

### `agent_selection_counts`

- Type: object
- Meaning: number of attempts made by each runtime agent.

### `average_agent_metrics`

- Type: object
- Meaning: average post-update metric values for each agent across its attempts.

### `agent_outcomes`

- Type: object
- Meaning: per-agent success/failure breakdown.

Each agent contains:

- `attempts`
- `successes`
- `failures`
- `failure_rate`
- `failure_types`

### `failure_counts`

- Type: object
- Meaning: total count of each failure type across the run.

### `format_failure_count`

- Type: integer
- Meaning: `invalid_json + schema_validation_failed`.

### `scenario_scores`

- Type: object
- Meaning: average scores grouped by scenario type.

Each scenario contains:

- `correctness`
- `completeness`
- `supportiveness`
- `reliability`

### `task_failure_overview`

- Type: array of objects
- Meaning: one summary row per task indicating who failed and who did not.

Each row contains:

- `iteration`
- `scenario_type`
- `question_count`
- `selected_agents`
- `failing_agents`
- `successful_agents`

### `aggregate_windows`

- Type: array of objects
- Meaning: rolling aggregate summaries over the configured window size.

Each window contains:

- `end_iteration`
- `failure_rate`
- `correctness`
- `completeness`
- `supportiveness`
- `reliability`

## 5. `config_snapshot.yaml`

This file stores the exact validated YAML config used for the run.

Use it when you want the canonical config file form. Use `run_metadata.json` or `summary.json` when you want the same information quickly in result form.

## 6. Where The Generated Exams Are Stored

Generated exams are stored in:

- `tasks.jsonl`, one task per iteration
- `experiment.jsonl`, under the `task` key on each iteration record

## 7. Files To Inspect First

If you want the fastest overview of a run:

1. Open `run_metadata.json`
2. Open `summary.json`
3. Open `tasks.jsonl`
4. Open the first few lines of `experiment.jsonl`
5. Open the plots in `analysis/`
