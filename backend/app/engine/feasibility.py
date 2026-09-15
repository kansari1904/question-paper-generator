"""
engine/feasibility.py

Stage 2 of the pipeline: feasibility check.

Takes the Targets object from validator.py and the loaded question bank,
and answers: "does the bank actually have enough questions to hit these
targets?" -- before Stage 3 (matrix_fit) wastes effort computing an ideal
distribution that can never be filled, and before Stage 4 (selector) has
to discover the gap mid-selection.

Feasibility is checked at three levels:
  1. Marginal supply per topic, per difficulty, per qtype (1D).
  2. Cell supply per (topic, difficulty, qtype) intersection (3D) -- this
     is where gaps like "Physics x Hard x Long only has 1 question" show up,
     even when the 1D marginals look fine in isolation.
  3. A rough upper bound check: can the qtype marginal even be reached
     given fixed per-question marks (MCQ=1/Short=3/Long=5)? A target of
     16 marks of MCQ needs at least 16 MCQ questions to exist in the bank.

Nothing here rejects the request outright. It produces a FeasibilityReport
that Stage 5 (resolver) uses to decide how to relax constraints. Silence is
never the output of this module -- every shortfall is a recorded Gap.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from app.models import Question, QuestionType, QTYPE_MARKS

from app.engine.validator import Targets


@dataclass
class Gap:
    """A single place where the bank cannot meet a target."""

    dimension: str  # e.g. "topic.Physics", "difficulty.Hard", "cell.Physics|Hard|Long"
    requested_marks: float
    available_marks: float
    shortfall_marks: float
    reason: str


@dataclass
class FeasibilityReport:
    is_fully_feasible: bool
    gaps: list[Gap] = field(default_factory=list)
    # Supply tables, exposed so Stage 3/4 don't need to recompute them.
    supply_by_topic: dict[str, int] = field(default_factory=dict)
    supply_by_difficulty: dict[str, int] = field(default_factory=dict)
    supply_by_qtype: dict[str, int] = field(default_factory=dict)
    supply_by_cell: dict[tuple[str, str, str], int] = field(default_factory=dict)


def _build_supply_tables(
    bank: list[Question],
) -> tuple[dict, dict, dict, dict]:
    by_topic: dict[str, int] = defaultdict(int)
    by_difficulty: dict[str, int] = defaultdict(int)
    by_qtype: dict[str, int] = defaultdict(int)
    by_cell: dict[tuple[str, str, str], int] = defaultdict(int)

    for q in bank:
        by_topic[q.topic.value] += q.marks
        by_difficulty[q.difficulty.value] += q.marks
        by_qtype[q.qtype.value] += q.marks
        by_cell[(q.topic.value, q.difficulty.value, q.qtype.value)] += q.marks

    return dict(by_topic), dict(by_difficulty), dict(by_qtype), dict(by_cell)


def check_feasibility(targets: Targets, bank: list[Question]) -> FeasibilityReport:
    """Compare requested marks targets against what the bank can supply."""
    supply_topic, supply_diff, supply_qtype, supply_cell = _build_supply_tables(bank)

    gaps: list[Gap] = []

    # --- 1D marginal checks -------------------------------------------------
    for topic, requested in targets.topic_marks.items():
        available = supply_topic.get(topic, 0)
        if requested > available:
            gaps.append(
                Gap(
                    dimension=f"topic.{topic}",
                    requested_marks=requested,
                    available_marks=available,
                    shortfall_marks=requested - available,
                    reason=(
                        f"Bank only has {available} marks worth of {topic} "
                        f"questions total, but {requested:.1f} were requested."
                    ),
                )
            )

    for difficulty, requested in targets.difficulty_marks.items():
        available = supply_diff.get(difficulty, 0)
        if requested > available:
            gaps.append(
                Gap(
                    dimension=f"difficulty.{difficulty}",
                    requested_marks=requested,
                    available_marks=available,
                    shortfall_marks=requested - available,
                    reason=(
                        f"Bank only has {available} marks worth of {difficulty} "
                        f"questions total, but {requested:.1f} were requested."
                    ),
                )
            )

    for qtype, requested in targets.qtype_marks.items():
        available = supply_qtype.get(qtype, 0)
        if requested > available:
            gaps.append(
                Gap(
                    dimension=f"qtype.{qtype}",
                    requested_marks=requested,
                    available_marks=available,
                    shortfall_marks=requested - available,
                    reason=(
                        f"Bank only has {available} marks worth of {qtype} "
                        f"questions total, but {requested:.1f} were requested."
                    ),
                )
            )

    # --- 3D cell checks (the sharp edges 1D checks can't see) ---------------
    # We estimate a naive per-cell demand as the product of the three
    # marginal proportions scaled to total_marks. This is a heuristic upper
    # bound used only to flag likely trouble spots for Stage 3; the actual
    # ideal cell targets are computed properly by matrix_fit.py via IPF.
    total = targets.total_marks
    for topic, topic_marks in targets.topic_marks.items():
        for difficulty, diff_marks in targets.difficulty_marks.items():
            for qtype, qtype_marks in targets.qtype_marks.items():
                if total == 0:
                    continue
                naive_cell_demand = (
                    (topic_marks / total) * (diff_marks / total) * (qtype_marks / total)
                ) * total
                cell_key = (topic, difficulty, qtype)
                cell_supply = supply_cell.get(cell_key, 0)
                min_question_cost = QTYPE_MARKS[QuestionType(qtype)]

                # Only surface a gap when the shortfall is at least one whole
                # question's worth of marks for this cell. The independence
                # formula above is a heuristic approximation (it assumes
                # topic/difficulty/qtype are statistically independent, which
                # the real selector does not require) -- sub-question-sized
                # gaps are rounding noise, not real infeasibility, and
                # flagging them would make the report cry wolf on requests
                # that are actually satisfiable.
                shortfall = naive_cell_demand - cell_supply
                if shortfall >= min_question_cost:
                    if cell_supply == 0:
                        reason = (
                            f"No {difficulty} {qtype} questions exist for "
                            f"{topic} in the bank, but the requested mix "
                            f"implies roughly {naive_cell_demand:.1f} marks "
                            f"should come from this combination."
                        )
                    else:
                        reason = (
                            f"{topic} {difficulty} {qtype} pool has only "
                            f"{cell_supply} marks available, roughly "
                            f"{naive_cell_demand:.1f} implied by the requested mix."
                        )
                    gaps.append(
                        Gap(
                            dimension=f"cell.{topic}|{difficulty}|{qtype}",
                            requested_marks=round(naive_cell_demand, 1),
                            available_marks=cell_supply,
                            shortfall_marks=round(shortfall, 1),
                            reason=reason,
                        )
                    )

    return FeasibilityReport(
        is_fully_feasible=(len(gaps) == 0),
        gaps=gaps,
        supply_by_topic=supply_topic,
        supply_by_difficulty=supply_diff,
        supply_by_qtype=supply_qtype,
        supply_by_cell=supply_cell,
    )
