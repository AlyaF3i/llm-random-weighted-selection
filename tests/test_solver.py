from __future__ import annotations

from llm_personality_experiment.tasks.models import MathExamTask, MathQuestion, OperationType, ScenarioType
from llm_personality_experiment.tasks.solver import solve_task


def test_solver_builds_answer_key() -> None:
    task = MathExamTask(
        task_id="exam-1",
        iteration=1,
        seed=1,
        scenario_type=ScenarioType.MIXED_REVIEW,
        grade_label="elementary school",
        instructions="Answer carefully.",
        questions=(
            MathQuestion("q1", "What is 2 + 3?", OperationType.ADDITION, (2, 3), 1),
            MathQuestion("q2", "What is 9 - 4?", OperationType.SUBTRACTION, (9, 4), 1),
            MathQuestion("q3", "What is 3 x 4?", OperationType.MULTIPLICATION, (3, 4), 1),
        ),
        total_points=3,
    )

    result = solve_task(task)

    assert result.answer_key == {"q1": "5", "q2": "5", "q3": "12"}
    assert result.total_points == 3
    assert result.question_count == 3
