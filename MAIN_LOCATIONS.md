# Main Code Locations

This file is a quick navigation guide for the most important sections of the project.

How to use it:

1. Open the file path shown below.
2. Search for the exact `# START: ...` text.
3. Read until the matching `# END: ...` text.

These markers were added to the code so you can jump directly to the section a doctor or professor asks about.

## Most Likely Questions

### Where does the experiment start and end?

File: `src/llm_personality_experiment/experiment/runner.py`

Search text:

- `# START: RUN-LEVEL ARTIFACT SETUP`
- `# START: MAIN EXPERIMENT LOOP`
- `# START: POST-RUN SUMMARY AND PLOT GENERATION`

### Where is one task generated?

File: `src/llm_personality_experiment/tasks/generator.py`

Search text:

- `# START: TASK GENERATION FOR ONE ITERATION`

### Where are the visible reference answers injected?

File: `src/llm_personality_experiment/tasks/generator.py`

Search text:

- `# START: REFERENCE ANSWER INJECTION FOR SHOWCASE TASKS`

### Where are personalities loaded and duplicated into multiple agents?

File: `src/llm_personality_experiment/experiment/runner.py`

Search text:

- `# START: PERSONALITY LOADING AND AGENT DUPLICATION`

### Where does agent selection start and end?

File: `src/llm_personality_experiment/experiment/runner.py`

Search text:

- `# START: AGENT SELECTION FOR CURRENT TASK`

Supporting selection internals:

File: `src/llm_personality_experiment/scoring/selection.py`

Search text:

- `# START: PREPARE WEIGHTS AND PROBABILITIES FOR SELECTION`
- `# START: EPSILON EXPLORATION VS WEIGHTED EXPLOITATION`
- `# START: EPSILON EXPLORATION BRANCH`
- `# START: WEIGHTED SAMPLING WITHOUT REPLACEMENT`

### Where are the current weights computed?

File: `src/llm_personality_experiment/scoring/selection.py`

Search text:

- `# START: WEIGHT COMPUTATION FOR ALL AGENTS`

### Where is the prompt built before calling the model?

File: `src/llm_personality_experiment/agents/client.py`

Search text:

- `# START: USER PROMPT CONSTRUCTION`

### Where is the actual model/backend call?

File: `src/llm_personality_experiment/agents/client.py`

Search text:

- `# START: BACKEND GENERATION CALL`

### Where does evaluation start and end?

High-level evaluation section:

File: `src/llm_personality_experiment/experiment/runner.py`

Search text:

- `# START: DETERMINISTIC VERIFICATION AND SCORE COMPUTATION`

Detailed verifier internals:

File: `src/llm_personality_experiment/tasks/verifier.py`

Search text:

- `# START: STRICT JSON PARSING`
- `# START: STRICT SCHEMA VALIDATION`
- `# START: ANSWER NORMALIZATION AND QUESTION-ID VALIDATION`
- `# START: DETERMINISTIC EXAM SCORING`
- `# START: FEEDBACK SUPPORTIVENESS AND RELIABILITY SCORING`

### Where are correctness, completeness, supportiveness, and reliability updated?

File: `src/llm_personality_experiment/scoring/updates.py`

Search text:

- `# START: BASELINE-AWARE METRIC UPDATE FOR ALL TRACKED METRICS`
- `# START: SINGLE METRIC UPDATE RULE`

### Where do you wait for all selected agents before committing updates?

File: `src/llm_personality_experiment/experiment/runner.py`

Search text:

- `# START: STAGE METRIC UPDATES UNTIL ALL SELECTED AGENTS FINISH`
- `# START: APPLY STAGED METRIC UPDATES AFTER ALL SELECTED AGENTS FINISH`

### Where are the logs written?

Task-level log before model execution:

File: `src/llm_personality_experiment/experiment/runner.py`

Search text:

- `# START: TASK-LEVEL RECORD BEFORE MODEL EXECUTION`

Full iteration JSONL log:

File: `src/llm_personality_experiment/experiment/runner.py`

Search text:

- `# START: ITERATION LOGGING WITH BEFORE AND AFTER STATES`

### Where is the config loaded and validated?

File: `src/llm_personality_experiment/config.py`

Search text:

- `# START: YAML CONFIG LOADING AND VALIDATION`

### Where is the config snapshot saved into the run folder?

File: `src/llm_personality_experiment/config.py`

Search text:

- `# START: CONFIG SNAPSHOT WRITING`

### Where is the run directory name created?

File: `src/llm_personality_experiment/experiment/runner.py`

Search text:

- `# START: RUN DIRECTORY NAMING AND OUTPUT PATH RESOLUTION`

### Where is the summary JSON produced after the run?

File: `src/llm_personality_experiment/analysis/summary.py`

Search text:

- `# START: RUN SUMMARY DATA LOADING`
- `# START: SUMMARY AGGREGATION ACROSS ALL ATTEMPTS`
- `# START: WINDOWED AGGREGATION FOR TREND REPORTING`
- `# START: SUMMARY OBJECT CONSTRUCTION`

## Full Marker Index

| Description | File | Search text |
| --- | --- | --- |
| Config load and validation | `src/llm_personality_experiment/config.py` | `# START: YAML CONFIG LOADING AND VALIDATION` |
| Config snapshot writing | `src/llm_personality_experiment/config.py` | `# START: CONFIG SNAPSHOT WRITING` |
| Prompt construction | `src/llm_personality_experiment/agents/client.py` | `# START: USER PROMPT CONSTRUCTION` |
| Backend model call | `src/llm_personality_experiment/agents/client.py` | `# START: BACKEND GENERATION CALL` |
| Summary input loading | `src/llm_personality_experiment/analysis/summary.py` | `# START: RUN SUMMARY DATA LOADING` |
| Summary aggregation | `src/llm_personality_experiment/analysis/summary.py` | `# START: SUMMARY AGGREGATION ACROSS ALL ATTEMPTS` |
| Windowed summary trends | `src/llm_personality_experiment/analysis/summary.py` | `# START: WINDOWED AGGREGATION FOR TREND REPORTING` |
| Summary object construction | `src/llm_personality_experiment/analysis/summary.py` | `# START: SUMMARY OBJECT CONSTRUCTION` |
| Run setup | `src/llm_personality_experiment/experiment/runner.py` | `# START: RUN-LEVEL ARTIFACT SETUP` |
| Main experiment loop | `src/llm_personality_experiment/experiment/runner.py` | `# START: MAIN EXPERIMENT LOOP` |
| Task generation and solver | `src/llm_personality_experiment/experiment/runner.py` | `# START: TASK GENERATION AND DETERMINISTIC SOLVER BASELINE` |
| Snapshot before selection | `src/llm_personality_experiment/experiment/runner.py` | `# START: AGENT STATE SNAPSHOT BEFORE SELECTION` |
| Agent selection | `src/llm_personality_experiment/experiment/runner.py` | `# START: AGENT SELECTION FOR CURRENT TASK` |
| Task log before model calls | `src/llm_personality_experiment/experiment/runner.py` | `# START: TASK-LEVEL RECORD BEFORE MODEL EXECUTION` |
| Selected-agent execution block | `src/llm_personality_experiment/experiment/runner.py` | `# START: SELECTED AGENT EXECUTION, EVALUATION, AND STAGED UPDATES` |
| Single agent attempt | `src/llm_personality_experiment/experiment/runner.py` | `# START: SINGLE AGENT ATTEMPT` |
| Model generation call in runner | `src/llm_personality_experiment/experiment/runner.py` | `# START: MODEL GENERATION CALL` |
| Verification and score computation | `src/llm_personality_experiment/experiment/runner.py` | `# START: DETERMINISTIC VERIFICATION AND SCORE COMPUTATION` |
| Stage metric updates | `src/llm_personality_experiment/experiment/runner.py` | `# START: STAGE METRIC UPDATES UNTIL ALL SELECTED AGENTS FINISH` |
| Apply staged updates | `src/llm_personality_experiment/experiment/runner.py` | `# START: APPLY STAGED METRIC UPDATES AFTER ALL SELECTED AGENTS FINISH` |
| Snapshot after evaluation | `src/llm_personality_experiment/experiment/runner.py` | `# START: AGENT STATE SNAPSHOT AFTER EVALUATION` |
| Iteration logging | `src/llm_personality_experiment/experiment/runner.py` | `# START: ITERATION LOGGING WITH BEFORE AND AFTER STATES` |
| Post-run summary and plots | `src/llm_personality_experiment/experiment/runner.py` | `# START: POST-RUN SUMMARY AND PLOT GENERATION` |
| Personality loading and duplication | `src/llm_personality_experiment/experiment/runner.py` | `# START: PERSONALITY LOADING AND AGENT DUPLICATION` |
| Run directory and artifact paths | `src/llm_personality_experiment/experiment/runner.py` | `# START: RUN DIRECTORY NAMING AND OUTPUT PATH RESOLUTION` |
| Weight computation | `src/llm_personality_experiment/scoring/selection.py` | `# START: WEIGHT COMPUTATION FOR ALL AGENTS` |
| Selection probabilities | `src/llm_personality_experiment/scoring/selection.py` | `# START: PREPARE WEIGHTS AND PROBABILITIES FOR SELECTION` |
| Exploration vs exploitation split | `src/llm_personality_experiment/scoring/selection.py` | `# START: EPSILON EXPLORATION VS WEIGHTED EXPLOITATION` |
| Pure exploration branch | `src/llm_personality_experiment/scoring/selection.py` | `# START: EPSILON EXPLORATION BRANCH` |
| Weighted sampling branch | `src/llm_personality_experiment/scoring/selection.py` | `# START: WEIGHTED SAMPLING WITHOUT REPLACEMENT` |
| Metric updates | `src/llm_personality_experiment/scoring/updates.py` | `# START: BASELINE-AWARE METRIC UPDATE FOR ALL TRACKED METRICS` |
| Single metric formula | `src/llm_personality_experiment/scoring/updates.py` | `# START: SINGLE METRIC UPDATE RULE` |
| Task generation | `src/llm_personality_experiment/tasks/generator.py` | `# START: TASK GENERATION FOR ONE ITERATION` |
| Reference answer injection | `src/llm_personality_experiment/tasks/generator.py` | `# START: REFERENCE ANSWER INJECTION FOR SHOWCASE TASKS` |
| JSON parsing | `src/llm_personality_experiment/tasks/verifier.py` | `# START: STRICT JSON PARSING` |
| Schema validation | `src/llm_personality_experiment/tasks/verifier.py` | `# START: STRICT SCHEMA VALIDATION` |
| Question ID validation | `src/llm_personality_experiment/tasks/verifier.py` | `# START: ANSWER NORMALIZATION AND QUESTION-ID VALIDATION` |
| Deterministic scoring | `src/llm_personality_experiment/tasks/verifier.py` | `# START: DETERMINISTIC EXAM SCORING` |
| Supportiveness and reliability scoring | `src/llm_personality_experiment/tasks/verifier.py` | `# START: FEEDBACK SUPPORTIVENESS AND RELIABILITY SCORING` |

## Best Sections To Show In A Live Demo

If you need to answer questions fast, open these first:

1. `src/llm_personality_experiment/experiment/runner.py`
2. `src/llm_personality_experiment/scoring/selection.py`
3. `src/llm_personality_experiment/tasks/verifier.py`
4. `src/llm_personality_experiment/scoring/updates.py`
5. `src/llm_personality_experiment/config.py`

That path covers the full story:

- config
- task
- selection
- model call
- evaluation
- metric update
- logging
- analysis output
