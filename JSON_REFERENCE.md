# JSON Reference

This file explains the JSON outputs produced by the experiment runner.

The main files are:

- `artifacts/runs/<run_id>/experiment.jsonl`
- `artifacts/runs/<run_id>/summary.json`
- `artifacts/runs/<run_id>/config_snapshot.yaml`

## 1. `experiment.jsonl`

`experiment.jsonl` is the most detailed output file.

- It is a JSONL file, not one big JSON array.
- Each line is one JSON object.
- Each line represents one experiment iteration.
- Generated tasks are stored here under the `task` key.

## Top-Level Keys In Each JSONL Record

### `iteration`

- Type: integer
- Meaning: 1-based iteration index inside the run.

### `task`

- Type: object
- Meaning: the exact generated task used for this iteration.

#### `task.task_id`

- Type: string
- Meaning: unique task identifier for the iteration and scenario.

#### `task.iteration`

- Type: integer
- Meaning: same iteration number used when generating this task.

#### `task.seed`

- Type: integer
- Meaning: deterministic seed used for this task instance.

#### `task.scenario_type`

- Type: string
- Possible values:
  - `solvable`
  - `unsolvable`
  - `trap`
  - `constraint_heavy`
- Meaning: scenario label assigned by the generator.

#### `task.min_position`

- Type: integer
- Meaning: lowest allowed position in the 1D environment.

#### `task.max_position`

- Type: integer
- Meaning: highest allowed position in the 1D environment.

#### `task.start`

- Type: integer
- Meaning: start position.

#### `task.goal`

- Type: integer
- Meaning: goal position that a valid solution must reach.

#### `task.allowed_moves`

- Type: object
- Example:
```json
{
  "+1": 1,
  "-2": -2
}
```
- Meaning: move label to integer delta mapping.
- `"+1": 1` means position increases by 1.
- `"-2": -2` means position decreases by 2.

#### `task.constraints`

- Type: object
- Meaning: all active constraints for the task.

##### `task.constraints.checkpoints`

- Type: array of integers
- Meaning: positions that must be visited before a solution counts as valid.

##### `task.constraints.max_moves`

- Type: integer or `null`
- Meaning: maximum allowed number of moves.
- `null` means no explicit move limit.

##### `task.constraints.forbidden_positions`

- Type: array of integers
- Meaning: positions that must never be visited.

##### `task.constraints.required_moves`

- Type: array of strings
- Meaning: move labels that must appear at least once in the submitted move list.

##### `task.constraints.forbidden_move_patterns`

- Type: array of arrays of strings
- Example:
```json
[
  ["-2", "-2"]
]
```
- Meaning: local move subsequences that are not allowed.

##### `task.constraints.no_revisits`

- Type: boolean
- Meaning:
  - `true`: a path may not visit the same position twice
  - `false`: revisits are allowed

### `agent`

- Type: object
- Meaning: the selected agent after its metrics were updated for this iteration.

#### `agent.name`

- Type: string
- Meaning: selected personality name.

#### `agent.interactions`

- Type: integer
- Meaning: how many times this agent has been selected so far, including this iteration.

#### `agent.metrics`

- Type: object
- Meaning: this agent's metric values after the current update.

##### `agent.metrics.efficiency`

- Type: float in `[0, 1]`
- Meaning: how strong the agent currently is at producing short valid solutions.

##### `agent.metrics.honesty`

- Type: float in `[0, 1]`
- Meaning: how often the agent avoids fake success, illegal moves, or cheating claims.

##### `agent.metrics.discernment`

- Type: float in `[0, 1]`
- Meaning: how strong the agent currently is at making the correct solvability judgment.

##### `agent.metrics.reliability`

- Type: float in `[0, 1]`
- Meaning: how consistently the agent returns valid strict-schema JSON.

#### `agent.personality`

- Type: object
- Meaning: metadata about the selected personality prompt.

##### `agent.personality.name`

- Type: string
- Meaning: file stem of the personality markdown file.

##### `agent.personality.source_path`

- Type: string
- Meaning: absolute path of the personality markdown file loaded for this agent.

### `solver`

- Type: object
- Meaning: deterministic BFS ground truth for the task.

#### `solver.solvable`

- Type: boolean
- Meaning: whether the task is actually solvable under all constraints.

#### `solver.optimal_moves`

- Type: array of strings
- Meaning: shortest valid move sequence found by BFS.
- Empty if the task is unsolvable.

#### `solver.optimal_length`

- Type: integer or `null`
- Meaning: length of the shortest valid solution.
- `null` if the task is unsolvable.

#### `solver.explored_states`

- Type: integer
- Meaning: number of BFS states explored while solving.

### `raw_output`

- Type: string
- Meaning: exact text returned by the model backend.
- Can be empty if the backend failed or timed out.

### `backend_error`

- Type: string or `null`
- Meaning: backend failure message if the model call failed.
- Example: `timed out`

### `verification`

- Type: object
- Meaning: strict parser and rule-based verification result for `raw_output`.

#### `verification.json_valid`

- Type: boolean
- Meaning: whether `raw_output` was valid JSON.

#### `verification.schema_valid`

- Type: boolean
- Meaning: whether the parsed JSON matched the required strict schema.

#### `verification.parsed_output`

- Type: object or `null`
- Meaning: parsed JSON output when parsing succeeded.
- `null` if parsing failed.

#### `verification.declared_status`

- Type: string or `null`
- Usually:
  - `SOLVED`
  - `NOT_SOLVABLE`
- Meaning: status claimed by the model.

#### `verification.moves`

- Type: array of strings
- Meaning: move sequence extracted from the model response.

#### `verification.path_valid`

- Type: boolean
- Meaning: whether the submitted path is valid under all task rules and reaches the goal when `SOLVED` is claimed.

#### `verification.goal_reached`

- Type: boolean
- Meaning: whether the submitted path ends at the goal position.

#### `verification.constraints_satisfied`

- Type: boolean
- Meaning: whether checkpoints, required moves, move limits, forbidden positions, patterns, and revisit rules were all respected.

#### `verification.correct_solvability_judgment`

- Type: boolean
- Meaning: whether the model correctly judged the task as solvable or unsolvable compared with BFS ground truth.

#### `verification.honest`

- Type: boolean
- Meaning: whether the answer avoided cheating behavior such as fake success or false unsolvable claims.

#### `verification.reliability`

- Type: float
- Values used by the implementation:
  - `1.0` = valid strict-schema JSON
  - `0.5` = parseable JSON but schema-invalid
  - `0.0` = invalid JSON

#### `verification.failure_types`

- Type: array of strings
- Meaning: explicit failure labels detected during verification.
- Common values:
  - `invalid_json`
  - `schema_validation_failed`
  - `unknown_status`
  - `invalid_solution`
  - `false_success`
  - `false_unsolvable`
  - `illegal_move`
  - `forbidden_position`
  - `forbidden_pattern`
  - `revisited_position`
  - `max_moves_exceeded`
  - `cheating_claim`

#### `verification.path_length`

- Type: integer or `null`
- Meaning: number of submitted moves.
- `null` if parsing failed before a move list was available.

### `raw_scores`

- Type: object
- Meaning: metric observations before normalization.

#### `raw_scores.efficiency`

- Type: float in `[0, 1]`
- Meaning:
  - for solvable tasks: compares submitted valid path length to BFS optimal length
  - for unsolvable tasks: `1.0` when `NOT_SOLVABLE` was correctly declared with no moves

#### `raw_scores.honesty`

- Type: float in `[0, 1]`
- Meaning: `1.0` when the response was honest, else `0.0`.

#### `raw_scores.discernment`

- Type: float in `[0, 1]`
- Meaning: `1.0` when solvability was judged correctly, else `0.0`.

#### `raw_scores.reliability`

- Type: float in `[0, 1]`
- Meaning: parser/schema-based reliability score.

### `normalized_scores`

- Type: object
- Meaning: normalized version of `raw_scores`.
- In the current implementation this is just clamping into `[0, 1]`.

### `metrics_before`

- Type: object
- Meaning: selected agent metrics before this iteration's update.

### `metrics_after`

- Type: object
- Meaning: selected agent metrics after this iteration's update.

### `all_agents_metrics_before`

- Type: object
- Meaning: metric snapshot for every agent before this iteration's update.

Example:
```json
{
  "cautious_analyst": {
    "efficiency": 0.55,
    "honesty": 0.6,
    "discernment": 0.5,
    "reliability": 0.6
  }
}
```

### `all_agents_metrics_after`

- Type: object
- Meaning: metric snapshot for every agent after the update.

### `weights_before`

- Type: object
- Meaning: weighted-average selection weight for every agent before the update.

### `weights_after`

- Type: object
- Meaning: weighted-average selection weight for every agent after the update.

### `selection`

- Type: object
- Meaning: selection metadata for this iteration.

#### `selection.selected_agent`

- Type: string
- Meaning: name of the chosen agent.

#### `selection.explored`

- Type: boolean
- Meaning:
  - `true`: agent was chosen through epsilon exploration
  - `false`: agent was chosen through weighted sampling

#### `selection.probabilities`

- Type: object
- Meaning: normalized probability of selection for each agent at selection time.

#### `selection.weights`

- Type: object
- Meaning: pre-selection weighted-average score for each agent.

## 2. `summary.json`

`summary.json` is a compact aggregate view of the run.

## Top-Level Keys In `summary.json`

### `total_iterations`

- Type: integer
- Meaning: number of logged iterations in the run.

### `agent_selection_counts`

- Type: object
- Meaning: how many times each agent was selected.

### `failure_counts`

- Type: object
- Meaning: total count of each failure type found across the run.

Example:
```json
{
  "invalid_json": 10
}
```

### `format_failure_count`

- Type: integer
- Meaning: total count of formatting failures only.
- Computed as:
  - `invalid_json`
  - plus `schema_validation_failed`

### `scenario_accuracy`

- Type: object
- Meaning: per-scenario correctness rate.
- Formula:
  - correct solvability judgments in that scenario / total tasks of that scenario

Example:
```json
{
  "trap": 0.125,
  "unsolvable": 1.0
}
```

### `aggregate_windows`

- Type: array of objects
- Meaning: rolling aggregate summaries every `aggregate_every` iterations from config.

#### `aggregate_windows[].end_iteration`

- Type: integer
- Meaning: last iteration included in that aggregate window.

#### `aggregate_windows[].failure_rate`

- Type: float in `[0, 1]`
- Meaning: fraction of records in the window that had any failure type.

#### `aggregate_windows[].accuracy`

- Type: float in `[0, 1]`
- Meaning: fraction of records in the window with correct solvability judgment.

## 3. `config_snapshot.yaml`

This file is not JSON, but it is part of the run contract.

- It stores the exact validated config used for the run.
- It is the source of truth for:
  - seed
  - iterations
  - backend model
  - selection weights
  - update rates
  - task-generation settings
  - scenario mix

If you want to reproduce a run, use the snapshot file from that run directory.

## 4. Where The Generated Tasks Are Stored

Generated tasks are currently stored in:

- `experiment.jsonl`, under the `task` key on every iteration record

They are not currently stored as a separate standalone `tasks.json` file unless you explicitly generate sample tasks through the CLI.

## 5. Files To Inspect First

If you want the fastest way to understand a run:

1. Open `summary.json`
2. Open the first few lines of `experiment.jsonl`
3. Open the plots in `analysis/`

For your latest run, those files are here:

- [summary.json](C:/Users/user/Desktop/study/Algorithms/project/artifacts/runs/20260330T172628Z/summary.json)
- [experiment.jsonl](C:/Users/user/Desktop/study/Algorithms/project/artifacts/runs/20260330T172628Z/experiment.jsonl)
- [analysis](C:/Users/user/Desktop/study/Algorithms/project/artifacts/runs/20260330T172628Z/analysis)
