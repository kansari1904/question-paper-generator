"""
engine/selector.py

Stage 4 of the pipeline: question selection.

Takes the ideal (topic, difficulty, qtype) marks matrix from matrix_fit.py
and picks actual Question objects from the bank to realize it.

Key simplification enabled by the fixed marks scheme (MCQ=1, Short=3,
Long=5): within a single cell, every question has the *same* mark value,
so "fill this cell with N marks" reduces to "pick round(N / fixed_marks)
questions from this cell" -- no combinatorial knapsack needed. This is
simpler and more predictable than a general knapsack, and it's an explicit
consequence of the assignment's marks assumption, not a shortcut we took
by accident.

Selection order: cells are processed largest-target-first, since big
chunks of marks are the ones most likely to cause a shortfall, and they
should get first pick of the bank while the most options remain.

Shortfall handling: if a cell can't supply enough questions, the deficit
is redistributed to the closest substitute cell in this priority order:
  1. Same topic, same qtype, adjacent difficulty (least perceptible swap)
  2. Same difficulty, same qtype, different topic
  3. Same qtype, any remaining cell
If none of those can absorb it either, the deficit is recorded as
unmet_marks and handed to resolver.py (Stage 5) to explain in the report.

Final reconciliation: total marks is the one hard constraint (per the
brief), so after all cells are filled the selector tops up or trims using
MCQ questions (the finest-grained, 1-mark unit) to land on total_marks
exactly, provided the bank has unused MCQs available.

Regeneration uses a seeded RNG: same seed -> same paper (reproducible for
debugging), different seed -> a different valid paper (for "regenerate").
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass, field

from models import Question, QuestionType, QTYPE_MARKS
from matrix_fit import MatrixFitResult, Cell, TOPICS, DIFFICULTIES, QTYPES

DIFFICULTY_ORDER = ["Easy", "Medium", "Hard"]


@dataclass
class SelectionResult:
    selected_question_ids: list[str] = field(default_factory=list)
    achieved_marks_by_cell: dict[Cell, int] = field(default_factory=dict)
    total_marks_achieved: int = 0
    unmet_marks_by_cell: dict[Cell, float] = field(default_factory=dict)
    substitutions: list[str] = field(default_factory=list)  # human-readable notes


def select_questions(
    matrix: MatrixFitResult,
    bank: list[Question],
    total_marks: int,
    seed: int = 42,
) -> SelectionResult:
    rng = random.Random(seed)

    bank_by_cell: dict[Cell, list[Question]] = defaultdict(list)
    for q in bank:
        bank_by_cell[(q.topic.value, q.difficulty.value, q.qtype.value)].append(q)
    for cell_qs in bank_by_cell.values():
        rng.shuffle(cell_qs)

    used_ids: set[str] = set()
    result = SelectionResult()

    # Track outstanding shortfall (in marks) per cell, to redistribute.
    shortfall: dict[Cell, float] = {}

    # --- Pass 1: base allocation via FLOOR, not round() ---------------------
    # Rounding each of the 27 cells independently to the nearest multiple of
    # its fixed mark value is lossy in aggregate: most individual cell
    # targets fall below one question's worth of marks when a modest total
    # is split across 27 cells, so round() sends the majority of them to 0.
    # In testing this threw away ~30% of total marks before any real supply
    # constraint was even hit -- silently violating the total-marks hard
    # constraint. Flooring first and tracking the fractional remainder lets
    # Pass 2 (below) redistribute the leftover using a largest-remainder
    # apportionment, which is the standard fix for exactly this problem
    # (the same method used to allocate parliamentary seats fairly).
    remainder_marks: dict[Cell, float] = {}
    cells_by_target = sorted(
        matrix.matrix.items(), key=lambda kv: kv[1], reverse=True
    )

    for cell, target_marks in cells_by_target:
        topic, difficulty, qtype = cell
        fixed_marks = QTYPE_MARKS[QuestionType(qtype)]
        base_count = int(target_marks // fixed_marks) if fixed_marks else 0

        picked = _take_available(bank_by_cell[cell], used_ids, base_count)
        for q in picked:
            result.selected_question_ids.append(q.id)
            used_ids.add(q.id)

        achieved = len(picked) * fixed_marks
        result.achieved_marks_by_cell[cell] = achieved

        deficit_count = base_count - len(picked)
        if deficit_count > 0:
            # Genuine supply shortfall (bank ran out), not a rounding gap.
            shortfall[cell] = deficit_count * fixed_marks
            remainder_marks[cell] = 0.0
        else:
            # Fully served at the floored count -- track the leftover
            # fraction of a question's worth of marks for Pass 2.
            remainder_marks[cell] = target_marks - achieved

    # --- Pass 2: largest-remainder bump-up -----------------------------------
    # Distribute the marks lost to flooring back out, giving priority to
    # cells with the largest leftover fraction of a question (closest to
    # deserving a whole extra question), bounded by remaining bank supply.
    matrix_total = sum(matrix.matrix.values())
    achieved_total = sum(result.achieved_marks_by_cell.values())
    leftover_budget = matrix_total - achieved_total

    ranked_by_remainder = sorted(
        remainder_marks.items(), key=lambda kv: kv[1], reverse=True
    )
    for cell, rem in ranked_by_remainder:
        if leftover_budget <= 0 or rem <= 0:
            continue
        fixed_marks = QTYPE_MARKS[QuestionType(cell[2])]
        if fixed_marks > leftover_budget + fixed_marks * 0.5:
            # Adding this cell's question would overshoot the remaining
            # budget by more than half a question -- skip, a smaller-cost
            # cell further down the ranked list is a better fit.
            continue
        picked = _take_available(bank_by_cell[cell], used_ids, 1)
        if picked:
            q = picked[0]
            result.selected_question_ids.append(q.id)
            used_ids.add(q.id)
            result.achieved_marks_by_cell[cell] = (
                result.achieved_marks_by_cell.get(cell, 0) + fixed_marks
            )
            leftover_budget -= fixed_marks

    # --- Redistribute shortfalls -------------------------------------------
    for cell, missing_marks in list(shortfall.items()):
        if missing_marks <= 0:
            continue
        topic, difficulty, qtype = cell
        fixed_marks = QTYPE_MARKS[QuestionType(qtype)]
        needed_count = round(missing_marks / fixed_marks)
        if needed_count <= 0:
            continue

        substitute_cells = _substitute_order(topic, difficulty, qtype)
        remaining_needed = needed_count

        for sub_cell in substitute_cells:
            if remaining_needed <= 0:
                break
            sub_fixed = QTYPE_MARKS[QuestionType(sub_cell[2])]
            if sub_fixed != fixed_marks:
                # Only substitute within the same qtype so the qtype mix
                # is never silently altered by a difficulty/topic fallback.
                continue
            picked = _take_available(bank_by_cell[sub_cell], used_ids, remaining_needed)
            for q in picked:
                result.selected_question_ids.append(q.id)
                used_ids.add(q.id)
                result.achieved_marks_by_cell[sub_cell] = (
                    result.achieved_marks_by_cell.get(sub_cell, 0) + fixed_marks
                )
            if picked:
                result.substitutions.append(
                    f"{len(picked)} question(s) needed for {topic}/{difficulty}/{qtype} "
                    f"were substituted from {sub_cell[0]}/{sub_cell[1]}/{sub_cell[2]} "
                    f"(insufficient supply in the original cell)."
                )
            remaining_needed -= len(picked)

        unmet = remaining_needed * fixed_marks
        if unmet > 0:
            result.unmet_marks_by_cell[cell] = unmet

    # --- Reconcile total marks (hard constraint) ----------------------------
    current_total = sum(result.achieved_marks_by_cell.values())
    result.total_marks_achieved = current_total
    _reconcile_total(result, bank_by_cell, used_ids, current_total, total_marks, rng)

    return result


def _take_available(
    pool: list[Question], used_ids: set[str], count: int
) -> list[Question]:
    if count <= 0:
        return []
    available = [q for q in pool if q.id not in used_ids]
    return available[:count]


def _substitute_order(topic: str, difficulty: str, qtype: str) -> list[Cell]:
    """Priority order of fallback cells for a shortfall, all sharing qtype."""
    order: list[Cell] = []

    # 1. Same topic, adjacent difficulty.
    idx = DIFFICULTY_ORDER.index(difficulty)
    adjacent = []
    if idx - 1 >= 0:
        adjacent.append(DIFFICULTY_ORDER[idx - 1])
    if idx + 1 < len(DIFFICULTY_ORDER):
        adjacent.append(DIFFICULTY_ORDER[idx + 1])
    for d in adjacent:
        order.append((topic, d, qtype))

    # 2. Same difficulty, different topic.
    for t in TOPICS:
        if t != topic:
            order.append((t, difficulty, qtype))

    # 3. Any remaining cell with the same qtype.
    for t in TOPICS:
        for d in DIFFICULTIES:
            cell = (t, d, qtype)
            if cell not in order and cell != (topic, difficulty, qtype):
                order.append(cell)

    return order


def _reconcile_total(
    result: SelectionResult,
    bank_by_cell: dict[Cell, list[Question]],
    used_ids: set[str],
    current_total: int,
    target_total: int,
    rng: random.Random,
) -> None:
    """Top up or trim using MCQ questions (1 mark each) so the paper lands
    on target_total exactly -- total marks is the one constraint that must
    never be violated, per the assignment brief."""
    diff = target_total - current_total
    if diff == 0:
        return

    if diff > 0:
        # Need more marks: add unused MCQ questions, any cell.
        mcq_cells = [c for c in bank_by_cell if c[2] == "MCQ"]
        rng.shuffle(mcq_cells)
        added = 0
        for cell in mcq_cells:
            if added >= diff:
                break
            for q in bank_by_cell[cell]:
                if added >= diff:
                    break
                if q.id not in used_ids:
                    result.selected_question_ids.append(q.id)
                    used_ids.add(q.id)
                    result.achieved_marks_by_cell[cell] = (
                        result.achieved_marks_by_cell.get(cell, 0) + 1
                    )
                    added += 1
        result.total_marks_achieved = current_total + added
        if added < diff:
            result.substitutions.append(
                f"Could not reach exact total_marks: needed {diff} more marks "
                f"but only {added} unused MCQ questions were available in the bank."
            )
    else:
        # Too many marks: remove MCQ questions already selected (safest,
        # finest-grained unit to trim without disturbing larger cells).
        to_remove = -diff
        removed = 0
        mcq_ids_in_paper = [
            qid for qid in result.selected_question_ids
            if _is_mcq(qid, bank_by_cell)
        ]
        for qid in mcq_ids_in_paper:
            if removed >= to_remove:
                break
            result.selected_question_ids.remove(qid)
            used_ids.discard(qid)
            removed += 1
        result.total_marks_achieved = current_total - removed
        if removed < to_remove:
            result.substitutions.append(
                f"Could not trim to exact total_marks: needed to remove "
                f"{to_remove} marks but only {removed} MCQ questions were "
                f"available to remove."
            )


def _is_mcq(question_id: str, bank_by_cell: dict[Cell, list[Question]]) -> bool:
    for cell, questions in bank_by_cell.items():
        if cell[2] == "MCQ":
            for q in questions:
                if q.id == question_id:
                    return True
    return False