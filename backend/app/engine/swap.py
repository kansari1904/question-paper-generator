from __future__ import annotations

from dataclasses import dataclass

from app.models import Question


@dataclass
class SwapResult:
    success: bool
    replaced_question_id: str
    new_question: Question | None
    updated_selection_ids: list[str]
    message: str


def swap_question(
    current_selection_ids: list[str],
    question_id_to_replace: str,
    bank_by_id: dict[str, Question],
) -> SwapResult:

    if question_id_to_replace not in current_selection_ids:
        return SwapResult(
            success=False,
            replaced_question_id=question_id_to_replace,
            new_question=None,
            updated_selection_ids=current_selection_ids,
            message=(f"Question {question_id_to_replace} is not part of this paper."),
        )

    old_question = bank_by_id[question_id_to_replace]

    used_ids = set(current_selection_ids)

    # ---------------------------------------------------------
    # Strict swap:
    #
    # Same:
    #   topic
    #   difficulty
    #   qtype
    #   marks
    #
    # Only the question itself changes.
    # ---------------------------------------------------------

    candidates = [
        question
        for question in bank_by_id.values()
        if (
            question.id not in used_ids
            and question.topic == old_question.topic
            and question.difficulty == old_question.difficulty
            and question.qtype == old_question.qtype
            and question.marks == old_question.marks
        )
    ]

    if not candidates:
        return SwapResult(
            success=False,
            replaced_question_id=question_id_to_replace,
            new_question=None,
            updated_selection_ids=current_selection_ids,
            message=(
                "No valid replacement is available. "
                f"The paper needs another unused "
                f"{old_question.topic.value} / "
                f"{old_question.difficulty.value} / "
                f"{old_question.qtype.value} question "
                f"worth {old_question.marks} marks. "
                "The original question was kept unchanged."
            ),
        )

    # Deterministic replacement.
    new_question = sorted(
        candidates,
        key=lambda q: q.id,
    )[0]

    updated_ids = [
        new_question.id if qid == question_id_to_replace else qid
        for qid in current_selection_ids
    ]

    return SwapResult(
        success=True,
        replaced_question_id=question_id_to_replace,
        new_question=new_question,
        updated_selection_ids=updated_ids,
        message=(
            f"Question replaced successfully with "
            f"{new_question.id}. "
            "Topic, difficulty, question type, and marks "
            "remain unchanged."
        ),
    )
