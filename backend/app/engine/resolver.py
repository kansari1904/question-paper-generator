from __future__ import annotations

from app.engine.exact_solver import ExactSelectionResult
from app.models import (
    ConstraintReport,
    Deviation,
    PaperRequest,
)


def build_constraint_report_from_selection(
    request: PaperRequest,
    targets,
    selection: ExactSelectionResult,
) -> ConstraintReport:

    deviations: list[Deviation] = []
    warnings: list[str] = []

    # ---------------------------------------------------------
    # Total marks
    # ---------------------------------------------------------

    if selection.total_marks_achieved != request.total_marks:
        deviations.append(
            Deviation(
                dimension="Total marks",
                requested_pct=100,
                actual_pct=(selection.total_marks_achieved / request.total_marks) * 100,
                reason="Total marks must be exact.",
            )
        )

    # ---------------------------------------------------------
    # Topic
    # ---------------------------------------------------------

    requested_topics = {
        "Physics": request.topic_weightage.physics,
        "Chemistry": request.topic_weightage.chemistry,
        "Biology": request.topic_weightage.biology,
    }

    for topic, requested_pct in requested_topics.items():
        actual_marks = selection.achieved_marks_by_topic[topic]

        actual_pct = (actual_marks / request.total_marks) * 100

        if abs(actual_pct - requested_pct) > 1e-9:
            deviations.append(
                Deviation(
                    dimension=f"Topic: {topic}",
                    requested_pct=requested_pct,
                    actual_pct=actual_pct,
                    reason=("Small difference caused by discrete question marks."),
                )
            )

    # ---------------------------------------------------------
    # Difficulty
    # ---------------------------------------------------------

    requested_difficulty = {
        "Easy": request.difficulty_mix.easy,
        "Medium": request.difficulty_mix.medium,
        "Hard": request.difficulty_mix.hard,
    }

    for difficulty, requested_pct in requested_difficulty.items():
        actual_marks = selection.achieved_marks_by_difficulty[difficulty]

        actual_pct = (actual_marks / request.total_marks) * 100

        if abs(actual_pct - requested_pct) > 1e-9:
            deviations.append(
                Deviation(
                    dimension=f"Difficulty: {difficulty}",
                    requested_pct=requested_pct,
                    actual_pct=actual_pct,
                    reason=("Small difference caused by discrete question marks."),
                )
            )

    # ---------------------------------------------------------
    # Question type
    # ---------------------------------------------------------

    requested_qtypes = {
        "MCQ": request.qtype_mix.mcq,
        "Short": request.qtype_mix.short,
        "Long": request.qtype_mix.long,
    }

    for qtype, requested_pct in requested_qtypes.items():
        actual_marks = selection.achieved_marks_by_qtype[qtype]

        actual_pct = (actual_marks / request.total_marks) * 100

        if abs(actual_pct - requested_pct) > 1e-9:
            deviations.append(
                Deviation(
                    dimension=f"Question type: {qtype}",
                    requested_pct=requested_pct,
                    actual_pct=actual_pct,
                    reason=("Small difference caused by discrete question marks."),
                )
            )

    if deviations:
        warnings.append(
            "Exact question-type distribution was mathematically impossible because"
            "MCQ, Short, and Long questions carry fixed marks of 1, 3, and 5 respectively."
        )

    return ConstraintReport(
        requested_total_marks=request.total_marks,
        actual_total_marks=selection.total_marks_achieved,
        deviations=deviations,
        warnings=warnings,
    )
