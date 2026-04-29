# LLM Personality Experiment

This repository implements a deterministic framework for comparing LLM personalities on elementary-school math exams. Each task is a generated exam, multiple agents can be invited to the same task, outputs are verified without another LLM, and agent-selection weights adapt over time from measured performance.

The implementation follows the repository requirements in `AGENTS.md` and `SPEC.md`:

- deterministic task generation
- deterministic answer-key solving
- strict JSON-only output validation
- baseline-aware metric updates
- epsilon-greedy weighted agent selection
- structured JSONL replay logs
- summary generation and plotting utilities

## Project Structure

```text
src/llm_personality_experiment/
  agents/          Personality loading, prompt construction, Ollama backend
  tasks/           Exam models, generator, deterministic solver, verifier
  scoring/         Metrics, normalization, updates, weighted selection
  experiment/      Main run loop and orchestration
  logging_utils/   JSONL logging
  analysis/        Summaries and plots
  utils/           Seed and I/O helpers
configs/
  easy_qwen.yaml   Main experiment config for local Ollama runs
  correctness_only_metric_average.yaml  Correctness-only baseline with metric-derived weights
  correctness_only_exponential.yaml  Correctness-only run with exponential weight updates
  personality_sampling.json  Per-personality sampling settings
personalities/
  *.md             Personality instruction files loaded at runtime
tests/
  Unit and runner smoke tests
```

## Requirements

- Python 3.10+
- Conda recommended; `environment.yml` pins Python 3.11
- Ollama for real model runs
- Tested local model family: `qwen3.5:9b`

Install with conda:

```powershell
conda env create -f environment.yml
conda activate llm-personality-exp
```

Or install directly:

```bash
pip install -e .[dev]
```

## How To Run

Pull the model first:

```powershell
ollama pull qwen3.5:9b
```

Generate sample exams:

```powershell
python -m llm_personality_experiment.cli generate-sample-tasks --config configs\easy_qwen.yaml --count 5
```

Run a full experiment:

```powershell
python -m llm_personality_experiment.cli run --config configs\easy_qwen.yaml
```

Run the two comparison experiments:

```powershell
python -m llm_personality_experiment.cli run --config configs\correctness_only_metric_average.yaml
python -m llm_personality_experiment.cli run --config configs\correctness_only_exponential.yaml
```

Or run both experiments plus the comparison charts in one step:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_correctness_comparison.ps1
```

If you want to use a specific Python executable instead of the active shell environment:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_correctness_comparison.ps1 -PythonExe C:\Users\user\miniconda3\envs\llm-personality-exp\python.exe
```

Analyze an existing run:

```powershell
python -m llm_personality_experiment.cli analyze --run-dir artifacts\runs\<run_id> --aggregate-every 10
```

Compare two completed runs:

```powershell
python -m llm_personality_experiment.cli compare-runs `
  --run-dir artifacts\runs\<metric_average_run_id> `
  --run-dir artifacts\runs\<exponential_run_id> `
  --label metric_average `
  --label exponential `
  --output-dir artifacts\comparisons\correctness_only_comparison
```

Replay a run live:

```powershell
python -m llm_personality_experiment.cli replay --run-dir artifacts\runs\<run_id> --family-view
```

Run tests:

```powershell
pytest -q
```

## Task Design

Each task is a deterministic elementary-school math exam.

Each exam contains:

- a `grade_label`
- a short instruction string
- a scenario type: `addition`, `subtraction`, `multiplication`, or `mixed_review`
- a configurable number of questions
- per-question point values

Each question contains:

- `question_id`
- `prompt`
- `operation`
- `operands`
- `points`

The task generator is deterministic by seed and iteration. For a fixed config and seed, the same iteration always produces the same exam.

### Scenario Types

- `addition`: all questions are addition
- `subtraction`: all questions are subtraction
- `multiplication`: all questions are multiplication
- `mixed_review`: operations are sampled from `mixed_operation_pool`

The generator is fully programmatic and does not rely on the model.

## Prompting Design

Personalities are loaded from `personalities/*.md`.

Each personality file is injected into the user prompt. The backend system prompt is intentionally left empty. The user prompt includes:

- the personality instructions
- the task payload
- the strict JSON contract
- rules about answering every question and giving brief supportive feedback

This means the experiment varies behavior through personality text without relying on separate system-prompt handling.

## Output Contract

Agents must return strict JSON only:

```json
{
  "submission": {
    "answers": [
      {"question_id": "q1", "answer": "12"},
      {"question_id": "q2", "answer": "7"}
    ],
    "feedback": "Great effort. Keep practicing and check each answer carefully."
  }
}
```

The verifier rejects:

- invalid JSON
- extra schema fields
- duplicate question IDs
- unknown question IDs
- missing feedback

No extra text is allowed outside the JSON object.

## Solver And Verifier

The solver is deterministic and builds the answer key directly from the exam questions.

The verifier:

- parses the JSON strictly with Pydantic
- normalizes submitted numeric answers
- checks each submitted answer against the answer key
- scores answered-question coverage
- scores supportive feedback with deterministic keyword rules
- records explicit failure types

No LLM is used for scoring or evaluation.

## Metrics

Each agent maintains four separate metrics:

- `correctness`
- `completeness`
- `supportiveness`
- `reliability`

These are never collapsed internally into a single stored score.

### Raw Score Mapping

For each attempt:

- `correctness`: `score_earned / total_points`
- `completeness`: `answered_count / question_count`
- `supportiveness`: deterministic feedback score from keyword and minimum-length checks
- `reliability`: `1.0` for valid strict-schema JSON, `0.5` for parseable but schema-invalid JSON, `0.0` for invalid JSON

Normalization currently clamps each metric into `[0, 1]`.

## Selection Method

The project supports two selection-weight rules.

### Metric-Derived Weights

Each agent has a weight computed from the configured metric weights.

Let:

- `c_i` = correctness
- `m_i` = completeness
- `s_i` = supportiveness
- `r_i` = reliability

and config weights:

- `a` for correctness
- `b` for completeness
- `c` for supportiveness
- `d` for reliability

Then:

```text
w_i = (a*c_i + b*m_i + c*s_i + d*r_i) / (a + b + c + d)
```

Selection is epsilon-greedy:

- with probability `epsilon`, choose uniformly at random
- otherwise choose by weighted sampling

The config key `selection.agents_per_task` controls how many agents are invited to the same task. Selection is done without replacement, so a task can be attempted by `k` distinct agents in the same iteration.

### Exponential Weights

When `selection.weight_update_rule: exponential`, the project keeps a direct selection weight for each agent and updates it multiplicatively after each iteration.

For each selected agent:

```text
reward_i = weighted_average(normalized_observation_i, metric_weights)
w_i <- w_i * exp(eta * reward_i)
```

After updating selected agents, all agent weights are renormalized so they sum to `1.0`.

This means:

- stronger observed reward increases future selection probability multiplicatively
- weaker agents fall behind through normalization
- `selection.exponential_eta` controls how aggressively the weights separate

This creates:

- one generated exam per iteration
- one selection event per iteration
- one `experiment.jsonl` record per iteration
- one `tasks.jsonl` record per iteration
- an `agent_attempts` array inside each iteration record

## Metric Update Equations

Each metric value `x_t` is updated from observation `s_t` relative to its configured baseline `b`.

If `x_t >= b`, use the `above_baseline` rates:

```text
if s_t >= x_t:
    x_(t+1) = clamp(x_t + inc_above * (s_t - x_t))
else:
    x_(t+1) = clamp(x_t - dec_above * (x_t - s_t))
```

If `x_t < b`, use the `below_baseline` rates:

```text
if s_t >= x_t:
    x_(t+1) = clamp(x_t + inc_below * (s_t - x_t))
else:
    x_(t+1) = clamp(x_t - dec_below * (x_t - s_t))
```

Where `clamp` restricts the result to `[min_value, max_value]`.

This allows configurable recovery and penalty behavior above and below baseline.

Even when `selection.weight_update_rule: exponential` is used, the metric state is still updated with these equations for logging and analysis. The difference is that future selection probabilities come from the direct exponential weights instead of being recomputed from metric state.

## Personality Duplication

All personality files are loaded from disk. The config can duplicate any personality with:

```yaml
personalities:
  duplication:
    always_correct: 2
    always_nice_teacher: 2
    sometimes_correct: 2
```

Duplicated agents are instantiated as separate runtime agents with names like:

- `always_correct__01`
- `always_correct__02`

They share the same prompt text but maintain independent metric histories.

Per-personality sampling settings are loaded from:

- `configs/personality_sampling.json`

That JSON defines:

- `temperature`
- `p_sample`
- `k_sample`

Use lower values for stricter, more deterministic personalities and higher values for personalities that should be more flexible or error-prone.

## Logging

Runs are stored under:

```text
artifacts/runs/<experiment_name>_<timestamp>/
```

Main files:

- `experiment.jsonl`
- `tasks.jsonl`
- `run_metadata.json`
- `summary.json`
- `config_snapshot.yaml`
- `analysis/*.png`

`experiment.jsonl` is the replay log. It now contains one record per task iteration and includes:

- `iteration`
- `run_metadata`
- `task`
- `solver`
- `all_agents_metrics_before`
- `all_agents_metrics_after`
- `weights_before`
- `weights_after`
- `selection`
- `agent_attempts`

Each entry in `agent_attempts` stores one invited agent's output, verification result, failures, and metrics before/after update.

`tasks.jsonl` stores the exact exams asked, one task per iteration, so the questions are easy to inspect without reading scoring data.

`run_metadata.json` stores the model and run settings directly in JSON form, including backend settings, selection policy, duplication config, and the full validated config dump. `summary.json` also includes the same metadata under `run_metadata`.

Per-personality sampling profiles are also stored in run metadata, so each run records exactly which `temperature`, `p_sample`, and `k_sample` values were used for each personality prompt.

## Analysis Outputs

The plotting utilities generate:

- `metrics_over_time.png`
- `weights_over_time.png`
- `failure_rates.png`
- `scenario_scores.png`
- `selection_counts.png`
- `exam_scores_over_time.png`
- `json_validity_over_time.png`
- `agent_failure_counts.png`
- `agent_success_rates.png`
- `question_volume_over_time.png`
- `failure_type_heatmap.png`
- `final_metric_snapshot.png`

Several plots include threshold-aware coloring or reference lines:

- metric plots use configured baselines
- selection and success/failure bar charts use run averages
- validity plots show a target threshold band

`summary.json` includes:

- `run_metadata`
- `total_tasks`
- `total_attempts`
- `agent_selection_counts`
- `average_agent_metrics`
- `agent_outcomes`
- `failure_counts`
- `format_failure_count`
- `scenario_scores`
- `task_failure_overview`
- `aggregate_windows`

## Configuration

All experiment parameters are loaded from YAML through the single config loader in `src/llm_personality_experiment/config.py`.

Key config areas:

- `experiment_name`: label used in the output folder name and stored in run metadata
- `backend`: Ollama model, URL, timeout, temperature, fallback `p_sample`, fallback `k_sample`
- `selection`: epsilon, metric weights, `agents_per_task`
- `selection.weight_update_rule`: choose between `metric_average` and `exponential`
- `selection.exponential_eta`: exponential update strength when the exponential rule is enabled
- `metrics`: initial values, baselines, min/max clamp
- `updates`: above-baseline and below-baseline rates
- `task_generation`: exam size, grade label, operation ranges, mixed pool
- `evaluation`: feedback-scoring keywords
- `scenario_mix`: relative frequencies of exam types
- `personalities.duplication`: per-personality replication count
- `personalities.sampling_parameters_path`: JSON file mapping each personality to its sampling settings
- `analysis`: window size and whether to generate plots automatically

There are no hardcoded experiment constants outside schema names and general program structure.

The repository keeps only these three personalities:

- `always_correct`
- `always_nice_teacher`
- `sometimes_correct`

## Assumptions And Design Decisions

- The task domain is deliberately narrow so correctness is fully measurable without another LLM.
- Feedback scoring is deterministic and keyword-based to keep evaluation reproducible.
- `supportiveness` is tracked separately from answer quality so helpful tone can be measured independently.
- Multi-agent selection uses the same exam for all selected agents in an iteration, making comparisons within a task direct.
- Personality duplication is treated as multiple independent bandit arms with identical prompt text.

## Testing

The test suite covers:

- deterministic exam generation
- solver correctness
- verifier behavior
- score computation
- baseline-aware updates
- multi-agent selection
- end-to-end runner behavior with a stub backend

## Related Docs

- `AGENTS.md`
- `SPEC.md`
- `JSON_REFERENCE.md`
- `AHMED.md`
