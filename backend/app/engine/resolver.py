"""
engine/resolver.py

Stage 5 of the pipeline: conflict resolution and reporting.

By the time this module runs, the actual relaxation work has already
happened implicitly through the pipeline's design:
  - matrix_fit.py (Stage 3) caps every cell at real bank supply during IPF,
    so the ideal matrix itself already respects hard capacity limits.
  - selector.py (Stage 4) redistributes shortfalls to the closest
    substitute cell in priority order (same topic/qtype + adjacent
    difficulty first, i.e. difficulty is sacrificed before topic or
    qtype), and reconciles total marks last using MCQ questions since
    total marks is the one constraint that must never be violated if the
    bank can possibly satisfy it.

resolver.py's job is therefore not to re-run selection, but to:
  1. Recompute what was actually achieved from the real selected questions
     (never trust intermediate estimates -- always verify against the
     final selected set).
  2. Compare achieved vs requested on every dimension.
  3. Explain every deviation with a concrete reason, in priority order,
     so nothing is silently dropped.
  4. Surface bank-improvement suggestions where a deviation traces back to
     a genuine supply gap (as opposed to a rounding effect, which by this
     stage should already be near zero thanks to Stage 4's largest-
     remainder apportionment).

Priority order (documented once here, applied throughout the pipeline):
    Total marks > Topic weightage > Question-type mix > Difficulty mix
Rationale: total marks is graded against a fixed scale and must be exact.
Topic weightage is usually syllabus-mandated by the school, making it the
most rigid pedagogical constraint after marks. Question-type mix is a
formatting choice. Difficulty mix is the most negotiable -- a paper that's
a little easier or harder than requested is a much smaller problem for a
teacher than one that under-represents a mandated topic or misses the
total marks.
"""

from __future__ import annotations

from collections import defaultdict

from app.models import (
    ConstraintReport,
    Deviation,
    PaperRequest,
    Question,
)
from app.engine.feasibility import FeasibilityReport
from app.engine.matrix_fit import MatrixFitResult
from app.engine.selector import SelectionResult
from app.engine.validator import Targets

TOLERANCE_PCT = 3.0  # percentage points; deviations smaller than this are not reported


def build_constraint_report(
    request: PaperRequest,
    targets: Targets,
    bank_by_id: dict[str, Question],
    feasibility: FeasibilityReport,
    matrix: MatrixFitResult,
    selection: SelectionResult,
) -> ConstraintReport:
    selected = [bank_by_id[qid] for qid in selection.selected_question_ids]
    actual_total = sum(q.marks for q in selected)

    deviations: list[Deviation] = []

    # --- 1. Total marks (highest priority; must be exact whenever possible) -
    if actual_total != targets.total_marks:
        deviations.append(
            Deviation(
                dimension="total_marks",
                requested_pct=100.0,
                actual_pct=round(100.0 * actual_total / targets.total_marks, 1)
                if targets.total_marks
                else 0.0,
                reason=(
                    f"Requested {targets.total_marks} marks, generated "
                    f"{actual_total} marks. {' '.join(selection.substitutions)}"
                    if selection.substitutions
                    else f"Requested {targets.total_marks} marks, generated {actual_total} marks."
                ),
            )
        )

    # --- Build evidence of genuine supply scarcity, per dimension ------------
    # Only dimensions with a real feasibility gap, an unmet cell, or a
    # logged substitution get attributed to "bank limit" in the report --
    # everything else is honestly attributed to the selector's own
    # apportionment trade-off (see _add_dimension_deviations docstring).
    topic_supply_evidence: dict[str, str] = {}
    qtype_supply_evidence: dict[str, str] = {}
    difficulty_supply_evidence: dict[str, str] = {}

    for gap in feasibility.gaps:
        if gap.dimension.startswith("topic."):
            topic_supply_evidence[gap.dimension.split(".", 1)[1]] = gap.reason
        elif gap.dimension.startswith("qtype."):
            qtype_supply_evidence[gap.dimension.split(".", 1)[1]] = gap.reason
        elif gap.dimension.startswith("difficulty."):
            difficulty_supply_evidence[gap.dimension.split(".", 1)[1]] = gap.reason
        elif gap.dimension.startswith("cell."):
            topic, difficulty, qtype = gap.dimension.split(".", 1)[1].split("|")
            topic_supply_evidence.setdefault(topic, gap.reason)
            qtype_supply_evidence.setdefault(qtype, gap.reason)
            difficulty_supply_evidence.setdefault(difficulty, gap.reason)

    for cell, unmet in selection.unmet_marks_by_cell.items():
        topic, difficulty, qtype = cell
        reason = (
            f"{unmet} marks for this cell could not be sourced anywhere in the bank."
        )
        topic_supply_evidence.setdefault(topic, reason)
        qtype_supply_evidence.setdefault(qtype, reason)
        difficulty_supply_evidence.setdefault(difficulty, reason)

    # --- 2. Topic weightage --------------------------------------------------
    actual_topic_marks: dict[str, int] = defaultdict(int)
    for q in selected:
        actual_topic_marks[q.topic.value] += q.marks
    _add_dimension_deviations(
        deviations,
        "topic",
        targets.topic_marks,
        actual_topic_marks,
        actual_total,
        supply_backed_reasons=topic_supply_evidence,
    )

    # --- 3. Question-type mix -------------------------------------------------
    actual_qtype_marks: dict[str, int] = defaultdict(int)
    for q in selected:
        actual_qtype_marks[q.qtype.value] += q.marks
    _add_dimension_deviations(
        deviations,
        "qtype",
        targets.qtype_marks,
        actual_qtype_marks,
        actual_total,
        supply_backed_reasons=qtype_supply_evidence,
    )

    # --- 4. Difficulty mix (lowest priority, most negotiable) ----------------
    actual_difficulty_marks: dict[str, int] = defaultdict(int)
    for q in selected:
        actual_difficulty_marks[q.difficulty.value] += q.marks
    _add_dimension_deviations(
        deviations,
        "difficulty",
        targets.difficulty_marks,
        actual_difficulty_marks,
        actual_total,
        supply_backed_reasons=difficulty_supply_evidence,
    )

    # --- Warnings: bank-improvement suggestions for genuine supply gaps ------
    warnings: list[str] = []
    for gap in feasibility.gaps:
        warnings.append(
            f"[bank limit] {gap.reason} Consider adding more questions to "
            f"this pool, or lowering the corresponding request percentage."
        )
    if matrix.unplaced_marks > 0:
        warnings.append(
            f"The ideal distribution could not fully place "
            f"{matrix.unplaced_marks} marks anywhere in the bank given the "
            f"requested mix; those marks were reassigned during selection "
            f"where possible."
        )
    for cell, unmet in selection.unmet_marks_by_cell.items():
        warnings.append(
            f"[unresolved] {unmet} marks intended for "
            f"{cell[0]}/{cell[1]}/{cell[2]} could not be sourced from any "
            f"substitute cell either -- the bank is exhausted for "
            f"comparable questions."
        )
    warnings.extend(selection.substitutions)

    return ConstraintReport(
        requested_total_marks=targets.total_marks,
        actual_total_marks=actual_total,
        deviations=deviations,
        warnings=warnings,
    )


def _add_dimension_deviations(
    deviations: list[Deviation],
    dimension_prefix: str,
    requested_marks: dict[str, float],
    actual_marks: dict[str, int],
    actual_total: int,
    supply_backed_reasons: dict[str, str] | None = None,
) -> None:
    """Add a Deviation for each key whose achieved % differs from requested
    % by more than TOLERANCE_PCT.

    supply_backed_reasons maps a key (e.g. "Physics", "Hard") to a concrete
    reason string ONLY when there is actual evidence of bank scarcity for
    it (a feasibility gap, an unmet cell, or a logged substitution). When no
    such evidence exists, the deviation is honestly attributed to the
    selector's own apportionment trade-off (Pass 2 optimizes for hitting
    the exact total-marks target and does not re-check per-axis drift
    afterward) rather than falsely blaming the bank. Claiming "limited by
    bank supply" without evidence would just relocate the assignment's
    warned-against failure mode (silently misrepresenting a constraint
    conflict) one layer deeper into the reporting code.
    """
    supply_backed_reasons = supply_backed_reasons or {}

    for key, requested in requested_marks.items():
        actual = actual_marks.get(key, 0)

        requested_pct_of_total = (
            100.0 * requested / sum(requested_marks.values())
            if sum(requested_marks.values())
            else 0.0
        )
        actual_pct_of_total = 100.0 * actual / actual_total if actual_total else 0.0

        if abs(requested_pct_of_total - actual_pct_of_total) > TOLERANCE_PCT:
            if key in supply_backed_reasons:
                # Gap.reason (feasibility.py) already ends in its own
                # period -- strip any trailing punctuation before splicing
                # it into this sentence so it never doubles up ("..").
                cause = supply_backed_reasons[key].rstrip(". ")
            else:
                cause = (
                    "not a bank shortage -- caused by the selector's final "
                    "apportionment pass, which prioritizes hitting the "
                    "exact total-marks target and can shift individual "
                    "topic/qtype/difficulty shares slightly in the process"
                )
            deviations.append(
                Deviation(
                    dimension=f"{dimension_prefix}.{key}",
                    requested_pct=round(requested_pct_of_total, 1),
                    actual_pct=round(actual_pct_of_total, 1),
                    reason=(
                        f"Requested {requested_pct_of_total:.1f}% {key} "
                        f"({requested:.1f} marks), achieved "
                        f"{actual_pct_of_total:.1f}% ({actual} marks) -- {cause}."
                    ),
                )
            )
