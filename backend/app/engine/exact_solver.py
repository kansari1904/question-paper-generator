from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp


@dataclass
class ExactSelectionResult:
    selected_question_ids: list[str]

    total_marks_achieved: int

    achieved_marks_by_topic: dict[str, int]

    achieved_marks_by_difficulty: dict[str, int]

    achieved_marks_by_qtype: dict[str, int]


class SolverError(Exception):
    """Raised when no valid paper can be generated."""


TOPICS = (
    "Physics",
    "Chemistry",
    "Biology",
)

DIFFICULTIES = (
    "Easy",
    "Medium",
    "Hard",
)

QTYPES = (
    "MCQ",
    "Short",
    "Long",
)


def solve_exact(
    questions: list,
    total_marks: int,
    difficulty_targets: dict[str, float],
    topic_targets: dict[str, float],
    qtype_targets: dict[str, float],
    seed: int = 42,
) -> ExactSelectionResult:
    """
    Generate a question paper using MILP.

    Rules:

    1. Total marks are always exact.
    2. Topic, difficulty, and question-type distributions are
       treated as target mark distributions.
    3. If exact targets are feasible, they are selected.
    4. If exact targets are mathematically impossible because
       of discrete question marks, the solver finds the closest
       feasible allocation.
    5. Zero-percent constraints remain exactly zero.
    6. No silent substitution between topic, difficulty, or qtype.
    """

    if not questions:
        raise SolverError("Question bank is empty.")

    if total_marks <= 0:
        raise SolverError("Total marks must be greater than zero.")

    rng = np.random.default_rng(seed)

    # ---------------------------------------------------------
    # Build the constraint matrix.
    # ---------------------------------------------------------

    question_count = len(questions)

    # First 10 rows:
    #
    # 0     total marks
    #
    # 1-3   topic marks
    #
    # 4-6   difficulty marks
    #
    # 7-9   question type marks
    #
    A = np.zeros((10, question_count), dtype=float)

    for i, question in enumerate(questions):
        marks = question.marks

        # Total
        A[0, i] = marks

        # Topic
        A[1, i] = marks if question.topic.value == "Physics" else 0
        A[2, i] = marks if question.topic.value == "Chemistry" else 0
        A[3, i] = marks if question.topic.value == "Biology" else 0

        # Difficulty
        A[4, i] = marks if question.difficulty.value == "Easy" else 0
        A[5, i] = marks if question.difficulty.value == "Medium" else 0
        A[6, i] = marks if question.difficulty.value == "Hard" else 0

        # Question type
        A[7, i] = marks if question.qtype.value == "MCQ" else 0
        A[8, i] = marks if question.qtype.value == "Short" else 0
        A[9, i] = marks if question.qtype.value == "Long" else 0

    # ---------------------------------------------------------
    # Requested decimal targets.
    # ---------------------------------------------------------

    target_values = np.array(
        [
            topic_targets["Physics"],
            topic_targets["Chemistry"],
            topic_targets["Biology"],
            difficulty_targets["Easy"],
            difficulty_targets["Medium"],
            difficulty_targets["Hard"],
            qtype_targets["MCQ"],
            qtype_targets["Short"],
            qtype_targets["Long"],
        ],
        dtype=float,
    )

    # ---------------------------------------------------------
    # Detect exact zero constraints.
    #
    # Example:
    #
    # Hard = 0%
    #
    # means absolutely no Hard questions are allowed.
    # ---------------------------------------------------------

    zero_rows = []

    for row_index, target in enumerate(target_values, start=1):
        if abs(target) < 1e-9:
            zero_rows.append(row_index)

    # ---------------------------------------------------------
    # Variables
    #
    # x_i = whether question i is selected
    #
    # d_j = absolute deviation for dimension j
    #
    # We have:
    #
    # question_count binary variables
    # +
    # 9 deviation variables
    # ---------------------------------------------------------

    deviation_count = 9

    variable_count = question_count + deviation_count

    # ---------------------------------------------------------
    # Objective
    #
    # Primary objective:
    #     minimize total absolute deviation.
    #
    # Secondary objective:
    #     tiny random value to make different seeds able to
    #     produce different valid papers when multiple papers
    #     have the same deviation.
    # ---------------------------------------------------------

    objective = np.zeros(variable_count, dtype=float)

    # Deviation variables dominate the random tie breaker.
    objective[question_count:] = 1.0

    # Small random tie breaker for question selection.
    objective[:question_count] = rng.random(question_count) * 1e-6

    # ---------------------------------------------------------
    # Equality constraint:
    #
    # Total marks must ALWAYS equal requested total marks.
    # ---------------------------------------------------------

    total_constraint = LinearConstraint(
        A=np.pad(
            A[0:1],
            ((0, 0), (0, deviation_count)),
            mode="constant",
        ),
        lb=np.array([total_marks], dtype=float),
        ub=np.array([total_marks], dtype=float),
    )

    constraints = [total_constraint]

    # ---------------------------------------------------------
    # Exact zero constraints.
    #
    # If requested percentage is 0%, actual marks must be 0.
    # ---------------------------------------------------------

    for row_index in zero_rows:
        row = np.zeros(variable_count, dtype=float)

        row[:question_count] = A[row_index]

        constraints.append(
            LinearConstraint(
                row,
                lb=np.array([0.0]),
                ub=np.array([0.0]),
            )
        )

    # ---------------------------------------------------------
    # Absolute deviation constraints.
    #
    # For every dimension:
    #
    # d >= actual - target
    # d >= target - actual
    #
    # Therefore:
    #
    # d = |actual - target|
    #
    # at the optimum.
    # ---------------------------------------------------------

    for dimension_index in range(deviation_count):
        row_index = dimension_index + 1

        actual_row = np.zeros(variable_count, dtype=float)
        actual_row[:question_count] = A[row_index]

        deviation_position = question_count + dimension_index

        # -----------------------------------------------------
        # d >= actual - target
        #
        # actual - d <= target
        # -----------------------------------------------------

        row_1 = actual_row.copy()
        row_1[deviation_position] = -1

        constraints.append(
            LinearConstraint(
                row_1,
                lb=-np.inf,
                ub=target_values[dimension_index],
            )
        )

        # -----------------------------------------------------
        # d >= target - actual
        #
        # -actual - d <= -target
        # -----------------------------------------------------

        row_2 = -actual_row
        row_2[deviation_position] = -1

        constraints.append(
            LinearConstraint(
                row_2,
                lb=-np.inf,
                ub=-target_values[dimension_index],
            )
        )

    # ---------------------------------------------------------
    # Bounds
    #
    # x_i:
    #     0 or 1
    #
    # d_j:
    #     >= 0
    # ---------------------------------------------------------

    lower_bounds = np.zeros(variable_count, dtype=float)

    upper_bounds = np.ones(variable_count, dtype=float)

    # Deviation variables can be larger than 1.
    upper_bounds[question_count:] = total_marks

    bounds = Bounds(
        lower_bounds,
        upper_bounds,
    )

    # Only question-selection variables are integer/binary.
    integrality = np.zeros(variable_count, dtype=int)
    integrality[:question_count] = 1

    # ---------------------------------------------------------
    # Solve
    # ---------------------------------------------------------

    result = milp(
        c=objective,
        integrality=integrality,
        bounds=bounds,
        constraints=constraints,
        options={
            "time_limit": 5,
        },
    )

    if not result.success:
        raise SolverError(
            "No valid question paper can satisfy the requested "
            "total marks and constraints with the current "
            "question bank. No substitutions were made."
        )

    # ---------------------------------------------------------
    # Extract selected questions.
    # ---------------------------------------------------------

    selected_indices = [
        i for i, value in enumerate(result.x[:question_count]) if value >= 0.5
    ]

    selected_questions = [questions[i] for i in selected_indices]

    # ---------------------------------------------------------
    # Safety check:
    #
    # Total marks MUST be exact.
    # ---------------------------------------------------------

    actual_total = sum(question.marks for question in selected_questions)

    if actual_total != total_marks:
        raise SolverError(
            "Internal solver error: generated paper does not "
            "match the requested total marks."
        )

    return build_selection_result(selected_questions)


def build_selection_result(
    questions: list,
) -> ExactSelectionResult:
    """
    Build selection statistics from a list of questions.

    This is also used after a successful question swap.
    """

    selected_ids = [question.id for question in questions]

    total_marks = sum(question.marks for question in questions)

    # ---------------------------------------------------------
    # Marks by topic
    # ---------------------------------------------------------

    topic_marks = {
        topic: sum(
            question.marks for question in questions if question.topic.value == topic
        )
        for topic in TOPICS
    }

    # ---------------------------------------------------------
    # Marks by difficulty
    # ---------------------------------------------------------

    difficulty_marks = {
        difficulty: sum(
            question.marks
            for question in questions
            if question.difficulty.value == difficulty
        )
        for difficulty in DIFFICULTIES
    }

    # ---------------------------------------------------------
    # Marks by question type
    # ---------------------------------------------------------

    qtype_marks = {
        qtype: sum(
            question.marks for question in questions if question.qtype.value == qtype
        )
        for qtype in QTYPES
    }

    return ExactSelectionResult(
        selected_question_ids=selected_ids,
        total_marks_achieved=total_marks,
        achieved_marks_by_topic=topic_marks,
        achieved_marks_by_difficulty=difficulty_marks,
        achieved_marks_by_qtype=qtype_marks,
    )
