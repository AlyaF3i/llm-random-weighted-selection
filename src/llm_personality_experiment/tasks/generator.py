"""Deterministic elementary-school math exam generator."""

from __future__ import annotations

from llm_personality_experiment.config import ExperimentConfig, OperationConfig
from llm_personality_experiment.tasks.models import MathExamTask, MathQuestion, OperationType, ScenarioType
from llm_personality_experiment.tasks.solver import solve_task
from llm_personality_experiment.utils.seed import create_rng


class TaskGenerator:
    """Generate scenario-labelled math exams reproducibly from the config."""

    def __init__(self, config: ExperimentConfig) -> None:
        self._config = config

    def generate(self, iteration: int, scenario_type: ScenarioType | None = None) -> MathExamTask:
        """Generate one validated task for the given iteration."""

        rng = create_rng(self._config.seed + (iteration * 7919))
        chosen_scenario = scenario_type or self._sample_scenario(rng)
        question_count = rng.randint(
            self._config.task_generation.questions_per_exam_min,
            self._config.task_generation.questions_per_exam_max,
        )
        questions = tuple(
            self._build_question(chosen_scenario, index + 1, rng)
            for index in range(question_count)
        )
        total_points = question_count * self._config.task_generation.points_per_question
        task = MathExamTask(
            task_id=f"exam-{iteration:05d}-{chosen_scenario.value}",
            iteration=iteration,
            seed=self._config.seed + iteration,
            scenario_type=chosen_scenario,
            grade_label=self._config.task_generation.grade_label,
            instructions=(
                "Answer each question with the final number only. "
                "Show care, keep it simple, and be encouraging in the feedback."
            ),
            questions=questions,
            total_points=total_points,
        )
        if self._config.task_generation.include_reference_answers:
            return MathExamTask(
                task_id=task.task_id,
                iteration=task.iteration,
                seed=task.seed,
                scenario_type=task.scenario_type,
                grade_label=task.grade_label,
                instructions=(
                    "Copy the provided reference_answers exactly unless your personality instructions tell you to do otherwise. "
                    "Still return the required JSON format."
                ),
                questions=task.questions,
                total_points=task.total_points,
                reference_answers=solve_task(task).answer_key,
            )
        return task

    def _sample_scenario(self, rng: object) -> ScenarioType:
        weights = self._config.scenario_mix
        total = sum(weights.values())
        threshold = getattr(rng, "random")() * total
        cumulative = 0.0
        for key, weight in weights.items():
            cumulative += weight
            if threshold <= cumulative:
                return ScenarioType(key)
        return ScenarioType(next(iter(weights)))

    def _build_question(self, scenario_type: ScenarioType, question_number: int, rng: object) -> MathQuestion:
        operation = self._choose_operation(scenario_type, rng)
        operation_config = self._config.task_generation.operations[operation.value]
        left, right = self._sample_operands(operation, operation_config, rng)
        prompt = self._build_prompt(operation, left, right)
        return MathQuestion(
            question_id=f"q{question_number}",
            prompt=prompt,
            operation=operation,
            operands=(left, right),
            points=self._config.task_generation.points_per_question,
        )

    def _choose_operation(self, scenario_type: ScenarioType, rng: object) -> OperationType:
        if scenario_type is ScenarioType.ADDITION:
            return OperationType.ADDITION
        if scenario_type is ScenarioType.SUBTRACTION:
            return OperationType.SUBTRACTION
        if scenario_type is ScenarioType.MULTIPLICATION:
            return OperationType.MULTIPLICATION
        operation_name = getattr(rng, "choice")(self._config.task_generation.mixed_operation_pool)
        return OperationType(operation_name)

    def _sample_operands(
        self,
        operation: OperationType,
        operation_config: OperationConfig,
        rng: object,
    ) -> tuple[int, int]:
        left = getattr(rng, "randint")(operation_config.min_operand, operation_config.max_operand)
        right = getattr(rng, "randint")(operation_config.min_operand, operation_config.max_operand)
        if operation is OperationType.SUBTRACTION and operation_config.non_negative_only and left < right:
            left, right = right, left
        return left, right

    def _build_prompt(self, operation: OperationType, left: int, right: int) -> str:
        symbol_map = {
            OperationType.ADDITION: "+",
            OperationType.SUBTRACTION: "-",
            OperationType.MULTIPLICATION: "x",
        }
        return f"What is {left} {symbol_map[operation]} {right}?"
