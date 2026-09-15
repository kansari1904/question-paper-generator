"""
engine/swap.py

Stage 7 of the pipeline: single-question swap.

This is intentionally isolated from the main generation pipeline (Stages
0-6) -- it never re-runs validation, feasibility, matrix fitting, or
selection. It only needs three things: the current paper's selected
question ids, the id of the question to replace, and the bank. That makes
a swap O(bank size) and near-instant, versus O(full pipeline) for a
regenerate.

Replacement priority (same logic as selector.py's shortfall
redistribution, reused here for consistency):
  1. Same topic, same difficulty, same qtype -- a perfect like-for-like
     swap. Always tried first and used whenever available.
  2. Same topic, same qtype, adjacent difficulty -- preserves the topic
     and the question's marks value exactly; the paper's total marks and
     topic weightage stay intact, only that one question's difficulty
     shifts slightly.
  3. Same difficulty, same qtype, different topic -- preserves difficulty
     and marks; topic weightage shifts slightly for this one question.
  4. Any other cell with the same qtype -- last resort before giving up;
     marks value is still preserved (so total marks never changes), but
     both topic and difficulty may differ from the original.
  5. Nothing available anywhere with the same qtype -- swap fails
     outright with an explanation. We never fall back to a different
     qtype, because that would silently change the question's marks
     value and therefore the paper's total -- the one constraint that
     must never be violated by a swap.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from app.models import Question, QuestionType, QTYPE_MARKS

Cell = tuple[str, str, str]
DIFFICULTY_ORDER = ["Easy", "Medium", "Hard"]
TOPICS = ("Physics", "Chemistry", "Biology")
DIFFICULTIES = ("Easy", "Medium", "Hard")


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
            message=f"Question {question_id_to_replace} is not part of this paper.",
        )

    old_q = bank_by_id[question_id_to_replace]
    topic, difficulty, qtype = (
        old_q.topic.value,
        old_q.difficulty.value,
        old_q.qtype.value,
    )

    used_ids = set(current_selection_ids)
    bank_by_cell: dict[Cell, list[Question]] = defaultdict(list)
    for q in bank_by_id.values():
        bank_by_cell[(q.topic.value, q.difficulty.value, q.qtype.value)].append(q)

    for cell, label in _candidate_cells(topic, difficulty, qtype):
        candidates = [q for q in bank_by_cell[cell] if q.id not in used_ids]
        if candidates:
            # Deterministic pick (first candidate) keeps swap results
            # reproducible; the frontend can offer "swap again" for variety.
            new_q = candidates[0]
            updated_ids = [
                new_q.id if qid == question_id_to_replace else qid
                for qid in current_selection_ids
            ]
            note = (
                f"Replaced with an exact match ({new_q.topic.value}/"
                f"{new_q.difficulty.value}/{new_q.qtype.value})."
                if label == "exact match"
                else f"No other {topic}/{difficulty}/{qtype} question was available, "
                f"so this was replaced from {new_q.topic.value}/"
                f"{new_q.difficulty.value}/{new_q.qtype.value} instead "
                f"({label}). Marks value is unchanged; {'topic' if new_q.topic.value != topic else 'difficulty'} differs from the original."
            )
            return SwapResult(
                success=True,
                replaced_question_id=question_id_to_replace,
                new_question=new_q,
                updated_selection_ids=updated_ids,
                message=note,
            )

    return SwapResult(
        success=False,
        replaced_question_id=question_id_to_replace,
        new_question=None,
        updated_selection_ids=current_selection_ids,
        message=(
            f"No replacement available: every {qtype} question in the bank "
            f"is already used in this paper. Add more {qtype} questions to "
            f"the bank, or remove another {qtype} question first to free "
            f"one up before swapping this one."
        ),
    )


def _candidate_cells(topic: str, difficulty: str, qtype: str) -> list[tuple[Cell, str]]:
    """Ordered (cell, label) pairs to try, matching selector.py's
    substitution priority so swap behaves consistently with generation."""
    order: list[tuple[Cell, str]] = [((topic, difficulty, qtype), "exact match")]

    idx = DIFFICULTY_ORDER.index(difficulty)
    adjacent = []
    if idx - 1 >= 0:
        adjacent.append(DIFFICULTY_ORDER[idx - 1])
    if idx + 1 < len(DIFFICULTY_ORDER):
        adjacent.append(DIFFICULTY_ORDER[idx + 1])
    for d in adjacent:
        order.append(((topic, d, qtype), "adjacent difficulty, same topic"))

    for t in TOPICS:
        if t != topic:
            order.append(((t, difficulty, qtype), "same difficulty, different topic"))

    for t in TOPICS:
        for d in DIFFICULTIES:
            cell = (t, d, qtype)
            if cell not in [c for c, _ in order]:
                order.append((cell, "different topic and difficulty"))

    return order
