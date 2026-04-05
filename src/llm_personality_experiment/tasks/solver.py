"""Deterministic exam answer-key builder."""

from __future__ import annotations

from llm_personality_experiment.tasks.models import ExamSolution, MathExamTask, OperationType


def solve_task(task: MathExamTask) -> ExamSolution:
    """Build the deterministic answer key for a math exam."""

    answer_key = {
        question.question_id: str(_compute_answer(question.operation, question.operands))
        for question in task.questions
    }
    return ExamSolution(
        answer_key=answer_key,
        total_points=task.total_points,
        question_count=len(task.questions),
    )


def _compute_answer(operation: OperationType, operands: tuple[int, int]) -> int:
    left, right = operands
    if operation is OperationType.ADDITION:
        return left + right
    if operation is OperationType.SUBTRACTION:
        return left - right
    if operation is OperationType.MULTIPLICATION:
        return left * right
    raise ValueError(f"Unsupported operation: {operation}")
