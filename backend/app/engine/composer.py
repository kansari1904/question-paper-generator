"""
engine/composer.py

Stage 6 of the pipeline: paper composition.

Takes the flat set of selected question ids (Stage 4's output, order
irrelevant) and arranges them the way a teacher actually structures a
paper:

  1. Grouped into sections by question type (MCQ, Short Answer, Long
     Answer), each with its own instructions line and marks subtotal --
     this is the single most recognizable structural feature of a real
     question paper and is what makes generated output feel authored
     rather than dumped.
  2. Within each section, ordered by rising difficulty (Easy -> Medium ->
     Hard) -- papers conventionally warm students up before the harder
     questions, never mix difficulty randomly.
  3. Within each difficulty band, topics are interleaved round-robin so
     the same topic never appears twice in a row, and where possible the
     same subtopic never repeats back-to-back either. Two "Laws of
     Motion" questions stacked next to each other reads as careless even
     if the marks/difficulty/topic percentages are all technically
     correct -- interleaving is what actually produces that "a teacher
     built this" feel the assignment asks for.

This module is a pure function over the selected Question objects -- no
randomness, no bank access beyond what's already been selected. Ordering
is deterministic given a selected set, so composing the same selection
twice always yields the same paper structure.
"""

from __future__ import annotations

from collections import defaultdict

from app.models import PaperSection, Question, QuestionType, QTYPE_MARKS

DIFFICULTY_ORDER = ["Easy", "Medium", "Hard"]
QTYPE_ORDER = ["MCQ", "Short", "Long"]
QTYPE_LABELS = {
    "MCQ": "Section A: Multiple Choice Questions",
    "Short": "Section B: Short Answer Questions",
    "Long": "Section C: Long Answer Questions",
}
QTYPE_INSTRUCTIONS = {
    "MCQ": "Choose the correct option for each question. 1 mark each.",
    "Short": "Answer briefly in 2-3 sentences. 3 marks each.",
    "Long": "Answer in detail with explanation/derivation as required. 5 marks each.",
}


def compose_paper(
    selected_ids: list[str], bank_by_id: dict[str, Question]
) -> tuple[list[PaperSection], list[Question]]:
    """Return (sections, ordered_questions) ready for PaperResponse."""
    selected = [bank_by_id[qid] for qid in selected_ids]

    by_qtype: dict[str, list[Question]] = defaultdict(list)
    for q in selected:
        by_qtype[q.qtype.value].append(q)

    sections: list[PaperSection] = []
    ordered_questions: list[Question] = []

    for qtype in QTYPE_ORDER:
        qs = by_qtype.get(qtype, [])
        if not qs:
            continue

        ordered_section_qs = _order_section(qs)
        marks_subtotal = sum(q.marks for q in ordered_section_qs)

        sections.append(
            PaperSection(
                qtype=QuestionType(qtype),
                instructions=(
                    f"{QTYPE_LABELS[qtype]} ({marks_subtotal} marks). "
                    f"{QTYPE_INSTRUCTIONS[qtype]}"
                ),
                marks_subtotal=marks_subtotal,
                question_ids=[q.id for q in ordered_section_qs],
            )
        )
        ordered_questions.extend(ordered_section_qs)

    return sections, ordered_questions


def _order_section(questions: list[Question]) -> list[Question]:
    """Order one qtype section: rising difficulty, topics interleaved
    within each difficulty band so no topic repeats back-to-back."""
    result: list[Question] = []
    by_difficulty: dict[str, list[Question]] = defaultdict(list)
    for q in questions:
        by_difficulty[q.difficulty.value].append(q)

    for difficulty in DIFFICULTY_ORDER:
        band = by_difficulty.get(difficulty, [])
        if band:
            result.extend(_interleave_by_topic(band))

    return result


def _interleave_by_topic(questions: list[Question]) -> list[Question]:
    """Round-robin merge questions across topics so the same topic never
    appears twice consecutively (when more than one topic is present).
    Within a topic's own queue, order by subtopic to reduce the chance
    of two near-identical questions landing back to back even after
    interleaving resolves the topic-level adjacency."""
    by_topic: dict[str, list[Question]] = defaultdict(list)
    for q in questions:
        by_topic[q.topic.value].append(q)
    for topic_qs in by_topic.values():
        topic_qs.sort(key=lambda q: (q.subtopic or "", q.id))

    queues = list(by_topic.values())
    result: list[Question] = []
    last_topic: str | None = None

    while any(queues):
        # Prefer the longest remaining queue whose topic differs from the
        # last placed question, to spread topics as evenly as possible.
        queues = [q for q in queues if q]
        queues.sort(key=len, reverse=True)

        placed = False
        for queue in queues:
            if queue[0].topic.value != last_topic:
                q = queue.pop(0)
                result.append(q)
                last_topic = q.topic.value
                placed = True
                break

        if not placed:
            # Only one topic left with items -- no way to avoid repeating it.
            q = queues[0].pop(0)
            result.append(q)
            last_topic = q.topic.value

    return result
