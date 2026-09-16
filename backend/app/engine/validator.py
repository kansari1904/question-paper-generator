from __future__ import annotations

from dataclasses import dataclass

from pydantic import ValidationError as PydanticValidationError

from app.models import PaperRequest, QTYPE_MARKS, QuestionType


class ValidationError(Exception):
    """Raised when the request is malformed or structurally unsatisfiable
    before any question bank lookup happens."""

    def __init__(self, message: str, field: str | None = None):
        self.field = field
        super().__init__(message)


@dataclass
class Targets:
    """Marks-based targets derived from a validated PaperRequest.

    All downstream stages (feasibility, matrix_fit, selector) consume this
    object rather than re-deriving percentages themselves.
    """

    total_marks: int
    difficulty_marks: dict[str, float]  # {"Easy": .., "Medium": .., "Hard": ..}
    topic_marks: dict[str, float]  # {"Physics": .., "Chemistry": .., "Biology": ..}
    qtype_marks: dict[str, float]  # {"MCQ": .., "Short": .., "Long": ..}


def parse_request(raw: dict) -> PaperRequest:
    """Parse and validate the raw teacher input.

    Raises ValidationError with a clean message on any structural problem
    (missing field, out-of-range %, mix not summing to 100, non-positive
    total marks, etc.) instead of leaking a raw Pydantic traceback.
    """
    try:
        return PaperRequest(**raw)
    except PydanticValidationError as e:
        first = e.errors()[0]
        field = ".".join(str(p) for p in first["loc"])
        raise ValidationError(
            f"Invalid input at '{field}': {first['msg']}", field=field
        ) from e


def compute_targets(request: PaperRequest) -> Targets:
    """Convert validated percentages into marks targets, anchored to
    total_marks exactly (Stage 1 of the pipeline)."""
    total = request.total_marks

    difficulty_marks = {
        "Easy": total * request.difficulty_mix.easy / 100,
        "Medium": total * request.difficulty_mix.medium / 100,
        "Hard": total * request.difficulty_mix.hard / 100,
    }
    topic_marks = {
        "Physics": total * request.topic_weightage.physics / 100,
        "Chemistry": total * request.topic_weightage.chemistry / 100,
        "Biology": total * request.topic_weightage.biology / 100,
    }
    qtype_marks = {
        "MCQ": total * request.qtype_mix.mcq / 100,
        "Short": total * request.qtype_mix.short / 100,
        "Long": total * request.qtype_mix.long / 100,
    }

    _check_qtype_reachability(qtype_marks, total)

    return Targets(
        total_marks=total,
        difficulty_marks=difficulty_marks,
        topic_marks=topic_marks,
        qtype_marks=qtype_marks,
    )


def _check_qtype_reachability(qtype_marks: dict[str, float], total: int) -> None:
    """Flag qtype targets that are structurally too small to produce even
    one question of that type (e.g. 2% Long on a 20-mark paper = 0.4 marks,
    but a Long question costs 5 marks minimum).

    This does NOT reject the request — Stage 5 (resolver) is responsible for
    deciding how to round/absorb this. It only raises when a target is so
    small relative to its question's fixed cost that rounding to zero
    questions would silently drop an entire requested question-type,
    which the teacher should be warned about up front rather than
    discovering in the constraint report.
    """
    for qtype_name, target in qtype_marks.items():
        qtype = QuestionType(qtype_name)
        min_cost = QTYPE_MARKS[qtype]
        if 0 < target < (min_cost / 2):
            raise ValidationError(
                f"Requested {qtype_name} share ({target:.1f} marks out of "
                f"{total}) is too small to produce even one {qtype_name} "
                f"question (costs {min_cost} marks). Increase total_marks, "
                f"increase the {qtype_name} percentage, or set it to 0%.",
                field=f"qtype_mix.{qtype_name.lower()}",
            )
