# JSON Reference

This file explains the output files produced by each run of the math-exam experiment.

Main files in a run directory:

- `artifacts/runs/<run_id>/experiment.jsonl`
- `artifacts/runs/<run_id>/summary.json`
- `artifacts/runs/<run_id>/run_metadata.json`
- `artifacts/runs/<run_id>/config_snapshot.yaml`

## 1. `run_metadata.json`

This file is the fastest way to see which model and config were used for a run.

Top-level keys:

### `run_id`

- Type: string
- Meaning: UTC timestamp-based run identifier, also used as the run folder name.

### `created_at_utc`

- Type: string
- Meaning: UTC creation timestamp stored in the same compact format as `run_id`.

### `backend`

- Type: object
- Meaning: backend settings used for the run.

Keys include:

- `provider`
- `base_url`
- `model_name`
- `timeout_seconds`
- `temperature`

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
- `loaded_agent_names`
- `loaded_personalities`
- `total_agents`

### `config`

- Type: object
- Meaning: full validated config dump used for the run.

## 2. `experiment.jsonl`

`experiment.jsonl` is the replay log.

- It is JSONL, not one large JSON array.
- Each line is one JSON object.
- Each line is one agent attempt.
- If `agents_per_task` is greater than `1`, the same `iteration` appears on multiple lines because multiple agents answered the same exam.

Generated exams are stored here under the `task` key.

## Top-Level Keys In Each JSONL Record

### `attempt_id`

- Type: integer
- Meaning: unique 1-based attempt counter across the run.

### `iteration`

- Type: integer
- Meaning: task iteration number. Multiple records can share the same value when more than one agent is invited.

### `run_metadata`

- Type: object
- Meaning: embedded run-level metadata so each record is self-describing even if separated from the run folder.
- Same structure as `run_metadata.json`.

### `task`

- Type: object
- Meaning: exact generated math exam used for this attempt.

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

- `question_id`: stable question identifier such as `q1`
- `prompt`: displayed math question text
- `operation`: `addition`, `subtraction`, or `multiplication`
- `operands`: two-number array serialized from the tuple
- `points`: integer points for the question

#### `task.total_points`

- Type: integer
- Meaning: total available score on the exam.

### `agent`

- Type: object
- Meaning: selected agent state after this attempt’s metric update.

#### `agent.name`

- Type: string
- Meaning: runtime agent name. Duplicated personalities are suffixed like `always_correct__01`.

#### `agent.interactions`

- Type: integer
- Meaning: how many times this agent has been selected so far, including this attempt.

#### `agent.metrics`

- Type: object
- Meaning: the agent’s metric values after the current update.

Metric keys:

- `correctness`
- `completeness`
- `supportiveness`
- `reliability`

#### `agent.personality`

- Type: object
- Meaning: personality metadata.

Keys:

- `name`
- `source_path`

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

### `raw_output`

- Type: string
- Meaning: exact raw model text returned by the backend.

### `backend_error`

- Type: string or `null`
- Meaning: backend failure message if the call failed.

### `verification`

- Type: object
- Meaning: strict parsing and deterministic grading result for `raw_output`.

#### `verification.json_valid`

- Type: boolean
- Meaning: whether the output parsed as JSON.

#### `verification.schema_valid`

- Type: boolean
- Meaning: whether the parsed JSON matched the strict schema.

#### `verification.parsed_output`

- Type: object or `null`
- Meaning: parsed JSON payload when available.

#### `verification.answers`

- Type: object
- Meaning: normalized submitted answers keyed by `question_id`.

#### `verification.feedback`

- Type: string or `null`
- Meaning: extracted feedback text.

#### `verification.answered_count`

- Type: integer
- Meaning: number of distinct valid question IDs answered.

#### `verification.correct_count`

- Type: integer
- Meaning: number of correct answers.

#### `verification.score_earned`

- Type: integer
- Meaning: total points earned by the submission.

#### `verification.total_points`

- Type: integer
- Meaning: total exam points available.

#### `verification.correctness_score`

- Type: float in `[0, 1]`
- Meaning: `score_earned / total_points`.

#### `verification.completeness_score`

- Type: float in `[0, 1]`
- Meaning: `answered_count / question_count`.

#### `verification.supportiveness_score`

- Type: float in `[0, 1]`
- Meaning: deterministic feedback-quality score.

Scoring factors:

- minimum word count
- presence of positive keywords
- presence of coaching keywords
- absence of banned keywords

#### `verification.reliability`

- Type: float
- Values used:
  - `1.0` = valid strict-schema JSON
  - `0.5` = parseable JSON but schema-invalid
  - `0.0` = invalid JSON

#### `verification.failure_types`

- Type: array of strings
- Meaning: explicit failure labels detected during parsing or grading.

Common values:

- `invalid_json`
- `schema_validation_failed`
- `duplicate_question_id`
- `unknown_question_id`
- `missing_feedback`

### `raw_scores`

- Type: object
- Meaning: direct metric observations before normalization.

Keys:

- `correctness`
- `completeness`
- `supportiveness`
- `reliability`

### `normalized_scores`

- Type: object
- Meaning: normalized version of `raw_scores`.
- Current behavior: clamp each value to `[0, 1]`.

### `metrics_before`

- Type: object
- Meaning: selected agent metrics before the update.

### `metrics_after`

- Type: object
- Meaning: selected agent metrics after the update.

### `all_agents_metrics_before`

- Type: object
- Meaning: metric snapshot for every agent before the update.

### `all_agents_metrics_after`

- Type: object
- Meaning: metric snapshot for every agent after the update.

### `weights_before`

- Type: object
- Meaning: selection weight for every agent before the update.

### `weights_after`

- Type: object
- Meaning: selection weight for every agent after the update.

### `selection`

- Type: object
- Meaning: selection metadata for the task-level invitation event.

#### `selection.selected_agents`

- Type: array of strings
- Meaning: all agents selected for the task in that iteration.
- The same array is repeated on each record generated from that iteration.

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

## 3. `summary.json`

`summary.json` is the aggregate run summary.

Top-level keys:

### `run_metadata`

- Type: object
- Meaning: same run metadata described above, included for quick inspection of model and config settings.

### `total_tasks`

- Type: integer
- Meaning: number of unique exam iterations in the run.

### `total_attempts`

- Type: integer
- Meaning: total number of logged agent attempts.

### `agent_selection_counts`

- Type: object
- Meaning: number of attempts made by each runtime agent.

### `average_agent_metrics`

- Type: object
- Meaning: average post-update metric values for each agent across its attempts.

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

## 4. `config_snapshot.yaml`

This file stores the exact validated YAML config used for the run.

Use it when you want the canonical config file form. Use `run_metadata.json` or `summary.json` when you want the same information quickly in result form.

## 5. Where The Generated Exams Are Stored

Generated exams are stored in:

- `experiment.jsonl`, under the `task` key on each attempt record

If multiple agents answer the same task, the same exam appears on multiple lines with the same `iteration`.

## 6. Files To Inspect First

If you want the fastest overview of a run:

1. Open `run_metadata.json`
2. Open `summary.json`
3. Open the first few lines of `experiment.jsonl`
4. Open the plots in `analysis/`
