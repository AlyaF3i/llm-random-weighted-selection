# Config Keys Reference

This file explains the configuration keys used by the experiment.

Main active config file:

`configs/easy_qwen.yaml`

Sampling profile file:

`configs/personality_sampling.json`

Schema source in code:

`src/llm_personality_experiment/config.py`

## Top-Level Keys In `easy_qwen.yaml`

| Key | Type | Meaning |
| --- | --- | --- |
| `experiment_name` | string | Human-readable experiment label. It is also used in the run folder name and stored in run metadata. |
| `seed` | integer | Base seed for deterministic task generation and selection randomness. Changing it changes the sampled tasks and selection path. |
| `iterations` | integer | Number of tasks to run in one experiment. With `agents_per_task: 3`, total attempts are `iterations * 3`. |
| `personalities_dir` | string | Folder that contains the personality prompt files loaded from `*.md`. |
| `personalities` | mapping | Personality duplication and per-personality sampling config. |
| `paths` | mapping | Output file and directory names for artifacts. |
| `backend` | mapping | Model provider and generation parameters used to call the LLM backend. |
| `selection` | mapping | Controls how agents are sampled for each task. |
| `metrics` | mapping | Initial metric values, baseline values, and min/max bounds. |
| `updates` | mapping | Learning-rate rules for moving metrics up or down after each attempt. |
| `task_generation` | mapping | Rules for generating the math exam tasks. |
| `evaluation` | mapping | Rules for scoring feedback quality and detecting banned language. |
| `scenario_mix` | mapping | Probability-like weights for which task scenario to generate. |
| `analysis` | mapping | Controls post-run summary and plot generation. |

## `personalities`

| Key | Type | Meaning |
| --- | --- | --- |
| `personalities.duplication` | mapping of string to integer | Number of agent copies to create for each personality file. Example: `always_correct: 2` creates `always_correct__01` and `always_correct__02`. |
| `personalities.sampling_parameters_path` | string | Path to the JSON file that stores per-personality `temperature`, `p_sample`, and `k_sample`. |

## `paths`

| Key | Type | Meaning |
| --- | --- | --- |
| `paths.output_root` | string | Root artifact folder. Usually `artifacts`. |
| `paths.runs_dirname` | string | Subdirectory under `output_root` that stores each run folder. |
| `paths.analysis_dirname` | string | Subdirectory inside each run that stores generated plots. |
| `paths.logs_filename` | string | Main JSONL file containing one record per task iteration. |
| `paths.tasks_filename` | string | JSONL file that stores the generated tasks and solver output before model execution. |
| `paths.metadata_filename` | string | JSON file that stores run metadata such as model, config, personalities, and timestamps. |
| `paths.config_snapshot_filename` | string | YAML snapshot of the validated config used for the run. |
| `paths.summary_filename` | string | JSON summary created after the run. |

## `backend`

| Key | Type | Meaning |
| --- | --- | --- |
| `backend.provider` | string | Backend type. In this project it is `ollama`. |
| `backend.base_url` | string | Base URL for the Ollama server. |
| `backend.model_name` | string | Exact model tag used for generation, for example `qwen3.5:9b`. |
| `backend.timeout_seconds` | float | Maximum time allowed for one model call before timing out. |
| `backend.temperature` | float | Default generation temperature used if a personality-specific value is not supplied. |
| `backend.p_sample` | float | Default top-p value used if a personality-specific value is not supplied. |
| `backend.k_sample` | integer | Default top-k value used if a personality-specific value is not supplied. |

## `selection`

| Key | Type | Meaning |
| --- | --- | --- |
| `selection.epsilon` | float between `0` and `1` | Exploration probability. If the random draw falls below `epsilon`, the system selects agents uniformly at random instead of by weights. |
| `selection.agents_per_task` | integer | Number of agents invited to answer each task. |
| `selection.weight_update_rule` | string | Selection-weight strategy. `metric_average` uses the weighted average of the tracked metrics. `exponential` keeps a direct selection weight per agent and updates it multiplicatively after each iteration. |
| `selection.exponential_eta` | float | Aggressiveness parameter for exponential selection-weight updates. Larger values make the weights separate faster. |
| `selection.metric_weights` | mapping | Weights used to collapse the four tracked metrics into one selection weight for sampling. |
| `selection.metric_weights.correctness` | float | Importance of academic correctness in selection. This is the strongest signal in the current showcase task. |
| `selection.metric_weights.completeness` | float | Importance of answering all questions. |
| `selection.metric_weights.supportiveness` | float | Importance of encouraging feedback tone. |
| `selection.metric_weights.reliability` | float | Importance of producing structurally valid outputs. |

## `metrics`

| Key | Type | Meaning |
| --- | --- | --- |
| `metrics.initial` | mapping | Starting values for the four tracked metrics before any tasks are run. |
| `metrics.initial.correctness` | float | Initial correctness metric. |
| `metrics.initial.completeness` | float | Initial completeness metric. |
| `metrics.initial.supportiveness` | float | Initial supportiveness metric. |
| `metrics.initial.reliability` | float | Initial reliability metric. |
| `metrics.baseline` | mapping | Reference values used by the update rules to decide whether an agent is currently above or below baseline. |
| `metrics.baseline.correctness` | float | Baseline correctness metric. |
| `metrics.baseline.completeness` | float | Baseline completeness metric. |
| `metrics.baseline.supportiveness` | float | Baseline supportiveness metric. |
| `metrics.baseline.reliability` | float | Baseline reliability metric. |
| `metrics.min_value` | float | Lower clamp bound for every metric. |
| `metrics.max_value` | float | Upper clamp bound for every metric. |

## `updates`

These keys define how quickly metrics move after each observation.

| Key | Type | Meaning |
| --- | --- | --- |
| `updates.above_baseline.increase_rate` | float | If the current metric is already above baseline and the new observation is better, this controls how fast it rises. |
| `updates.above_baseline.decrease_rate` | float | If the current metric is above baseline and the new observation is worse, this controls how fast it falls. |
| `updates.below_baseline.increase_rate` | float | If the current metric is below baseline and the new observation is better, this controls recovery speed. |
| `updates.below_baseline.decrease_rate` | float | If the current metric is below baseline and the new observation is worse, this controls penalty speed. |

## `task_generation`

| Key | Type | Meaning |
| --- | --- | --- |
| `task_generation.grade_label` | string | Human-readable label for the exam difficulty or grade band. |
| `task_generation.questions_per_exam_min` | integer | Minimum number of questions in one generated exam. |
| `task_generation.questions_per_exam_max` | integer | Maximum number of questions in one generated exam. |
| `task_generation.points_per_question` | integer | Points assigned to each question. |
| `task_generation.include_reference_answers` | boolean | If `true`, the task payload includes `reference_answers`. This is useful for showcase runs where the goal is to demonstrate weighting rather than reasoning difficulty. |
| `task_generation.operations` | mapping | Operand-generation rules for each operation family. |
| `task_generation.mixed_operation_pool` | list of strings | Which operations are allowed when the `mixed_review` scenario is generated. |

## `task_generation.operations.addition`

The same structure is used for `subtraction` and `multiplication`.

| Key | Type | Meaning |
| --- | --- | --- |
| `task_generation.operations.addition.min_operand` | integer | Smallest operand value that may appear. |
| `task_generation.operations.addition.max_operand` | integer | Largest operand value that may appear. |
| `task_generation.operations.addition.non_negative_only` | boolean | For subtraction, this prevents negative results by swapping operands if needed. It is harmless for addition and multiplication but kept consistent across operations. |

## `evaluation`

| Key | Type | Meaning |
| --- | --- | --- |
| `evaluation.feedback.positive_keywords` | list of strings | Words or phrases that increase the supportiveness score. |
| `evaluation.feedback.coaching_keywords` | list of strings | Words or phrases that indicate constructive coaching and also increase supportiveness. |
| `evaluation.feedback.banned_keywords` | list of strings | Words or phrases that force supportiveness to `0.0` if they appear in feedback. |
| `evaluation.feedback.min_words` | integer | Minimum feedback length needed to receive the basic supportiveness score. |

## `scenario_mix`

| Key | Type | Meaning |
| --- | --- | --- |
| `scenario_mix.addition` | float | Relative weight for generating addition tasks. |
| `scenario_mix.subtraction` | float | Relative weight for generating subtraction tasks. |
| `scenario_mix.multiplication` | float | Relative weight for generating multiplication tasks. |
| `scenario_mix.mixed_review` | float | Relative weight for generating mixed-operation tasks. |

These values do not need to sum to `1.0`, but they must all be non-negative and their total must be positive. They are treated as sampling weights.

## `analysis`

| Key | Type | Meaning |
| --- | --- | --- |
| `analysis.aggregate_every` | integer | Window size used when building trend summaries in `summary.json`. |
| `analysis.generate_after_run` | boolean | If `true`, plots are generated automatically at the end of the run. |

## Keys In `configs/personality_sampling.json`

This file lets you set generation flexibility separately for each personality.

Top-level keys:

- `default`
- `always_correct`
- `always_nice_teacher`
- `sometimes_correct`

Each personality entry uses the same fields:

| Key | Type | Meaning |
| --- | --- | --- |
| `temperature` | float | Controls randomness. Lower values make outputs more deterministic. |
| `p_sample` | float | Top-p sampling threshold. Lower values narrow the candidate token pool. |
| `k_sample` | integer | Top-k sampling limit. Lower values reduce flexibility. |

## Current Sampling Intent

| Personality | Intent |
| --- | --- |
| `always_correct` | Very low flexibility so it stays deterministic and follows the reference answers closely. |
| `always_nice_teacher` | Moderate flexibility so it keeps a supportive tone while still following its personality. |
| `sometimes_correct` | Higher flexibility so it is more likely to behave inconsistently and produce mixed outcomes. |

## Best Keys To Mention In A Presentation

If someone asks which keys matter most for the experiment story, mention these first:

- `experiment_name`
- `iterations`
- `selection.epsilon`
- `selection.agents_per_task`
- `selection.metric_weights.correctness`
- `metrics.initial.*`
- `metrics.baseline.*`
- `updates.above_baseline.*`
- `updates.below_baseline.*`
- `task_generation.include_reference_answers`
- `scenario_mix.*`
- `backend.model_name`
- `personalities.duplication`
- `personalities.sampling_parameters_path`

These keys control the main experiment behavior, the adaptive weighting logic, and the reproducibility of the run.
