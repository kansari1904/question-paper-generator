"""
engine/matrix_fit.py

Stage 3 of the pipeline: matrix fitting.

The teacher gives three independent 1D constraints (difficulty mix, topic
weightage, qtype mix). A real paper is a 3D grid of
(topic x difficulty x qtype) cells, and satisfying all three marginals
*simultaneously* is the actual hard problem -- three 1D targets can each be
satisfiable on their own while their intersection is not.

This module computes an ideal marks matrix via a capped version of
Iterative Proportional Fitting (IPF): a standard technique for filling a
table to match given marginal sums. The "capped" part is our addition --
plain IPF assumes unlimited capacity per cell, but we cannot ask for more
marks from a cell than the question bank actually has, so every scaling
step is clipped to supply_by_cell before the next axis is scaled.

This is a pure function: no I/O, no bank access beyond the supply numbers
already computed by feasibility.py. That keeps it independently unit
testable and keeps randomness/selection concerns out of it entirely --
selector.py (Stage 4) decides *which* questions fill a cell; this module
only decides *how many marks* each cell should ideally hold.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.engine.validator import Targets

Cell = tuple[str, str, str]  # (topic, difficulty, qtype)

TOPICS = ("Physics", "Chemistry", "Biology")
DIFFICULTIES = ("Easy", "Medium", "Hard")
QTYPES = ("MCQ", "Short", "Long")


@dataclass
class MatrixFitResult:
    # Ideal marks target per (topic, difficulty, qtype) cell, capped by supply.
    matrix: dict[Cell, float] = field(default_factory=dict)
    # How close each marginal ended up vs. what was requested, after capping.
    achieved_topic_marks: dict[str, float] = field(default_factory=dict)
    achieved_difficulty_marks: dict[str, float] = field(default_factory=dict)
    achieved_qtype_marks: dict[str, float] = field(default_factory=dict)
    # Marks that could not be placed anywhere due to supply caps -- this is
    # the quantity Stage 5 (resolver) needs in order to explain deviations.
    unplaced_marks: float = 0.0
    converged: bool = True


def fit_matrix(
    targets: Targets,
    supply_by_cell: dict[Cell, int],
    iterations: int = 25,
    tolerance: float = 0.05,
) -> MatrixFitResult:
    """Compute an ideal (topic, difficulty, qtype) marks matrix via capped IPF.

    Args:
        targets: marks targets per dimension, from validator.compute_targets.
        supply_by_cell: max marks available per cell, from
            feasibility.check_feasibility(...).supply_by_cell.
        iterations: max IPF sweeps (topic -> difficulty -> qtype -> repeat).
        tolerance: stop early once every marginal is within this many marks
            of its target.
    """
    all_cells: list[Cell] = [
        (t, d, q) for t in TOPICS for d in DIFFICULTIES for q in QTYPES
    ]
    total = targets.total_marks

    # --- Seed matrix: independence assumption, i.e. cell share is the
    # product of each marginal's proportion of the total. This is just a
    # starting point for IPF to refine, not the final answer.
    matrix: dict[Cell, float] = {}
    for t, d, q in all_cells:
        p_topic = targets.topic_marks[t] / total if total else 0
        p_diff = targets.difficulty_marks[d] / total if total else 0
        p_qtype = targets.qtype_marks[q] / total if total else 0
        seed = p_topic * p_diff * p_qtype * total
        cap = supply_by_cell.get((t, d, q), 0)
        matrix[(t, d, q)] = min(seed, cap)

    converged = False
    for _ in range(iterations):
        _scale_axis(
            matrix, targets.topic_marks, supply_by_cell, axis=0, all_cells=all_cells
        )
        _scale_axis(
            matrix,
            targets.difficulty_marks,
            supply_by_cell,
            axis=1,
            all_cells=all_cells,
        )
        _scale_axis(
            matrix, targets.qtype_marks, supply_by_cell, axis=2, all_cells=all_cells
        )

        if _within_tolerance(matrix, targets, tolerance):
            converged = True
            break

    achieved_topic = {t: 0.0 for t in TOPICS}
    achieved_diff = {d: 0.0 for d in DIFFICULTIES}
    achieved_qtype = {q: 0.0 for q in QTYPES}
    for (t, d, q), marks in matrix.items():
        achieved_topic[t] += marks
        achieved_diff[d] += marks
        achieved_qtype[q] += marks

    placed_total = sum(matrix.values())
    unplaced = max(0.0, total - placed_total)

    return MatrixFitResult(
        matrix=matrix,
        achieved_topic_marks=achieved_topic,
        achieved_difficulty_marks=achieved_diff,
        achieved_qtype_marks=achieved_qtype,
        unplaced_marks=round(unplaced, 2),
        converged=converged,
    )


def _scale_axis(
    matrix: dict[Cell, float],
    axis_targets: dict[str, float],
    supply_by_cell: dict[Cell, int],
    axis: int,
    all_cells: list[Cell],
) -> None:
    """One IPF sweep along a single axis (topic, difficulty, or qtype).

    For each value on this axis (e.g. each topic), sum the current matrix
    over the other two axes, compute a scale factor to hit that value's
    target, apply it to every cell on that slice, then clip to supply.
    Clipping is what makes this "capped" IPF -- without it, a thin cell
    could be asked to absorb more marks than any real question provides.
    """
    axis_values = set(cell[axis] for cell in all_cells)

    for value in axis_values:
        slice_cells = [c for c in all_cells if c[axis] == value]
        current_sum = sum(matrix[c] for c in slice_cells)
        target = axis_targets.get(value, 0)

        if current_sum <= 0 or target <= 0:
            continue

        scale = target / current_sum
        for c in slice_cells:
            scaled = matrix[c] * scale
            cap = supply_by_cell.get(c, 0)
            matrix[c] = min(scaled, cap)


def _within_tolerance(
    matrix: dict[Cell, float], targets: Targets, tolerance: float
) -> bool:
    achieved_topic = {t: 0.0 for t in TOPICS}
    achieved_diff = {d: 0.0 for d in DIFFICULTIES}
    achieved_qtype = {q: 0.0 for q in QTYPES}
    for (t, d, q), marks in matrix.items():
        achieved_topic[t] += marks
        achieved_diff[d] += marks
        achieved_qtype[q] += marks

    for t in TOPICS:
        if (
            abs(achieved_topic[t] - targets.topic_marks[t])
            > tolerance * targets.total_marks
        ):
            return False
    for d in DIFFICULTIES:
        if (
            abs(achieved_diff[d] - targets.difficulty_marks[d])
            > tolerance * targets.total_marks
        ):
            return False
    for q in QTYPES:
        if (
            abs(achieved_qtype[q] - targets.qtype_marks[q])
            > tolerance * targets.total_marks
        ):
            return False
    return True
