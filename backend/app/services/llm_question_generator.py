from __future__ import annotations

import json
import os

from langchain_groq import ChatGroq
from pydantic import ValidationError

from app.models import Question, QuestionSource, QTYPE_MARKS


PROMPT_TEMPLATE = """
You are generating one new school Science question for a
question-paper generator.

Generate exactly ONE question with these constraints:

Topic: {topic}
Difficulty: {difficulty}
Question Type: {qtype}
Marks: {marks}

Existing questions that MUST NOT be duplicated:

{existing_questions}

Rules:

1. Return ONLY valid JSON.
2. Do not return markdown.
3. The question must be suitable for Class 9-10 CBSE Science.
4. The question must be factually accurate.
5. The question must be different from all existing questions.
6. Keep the same topic, difficulty, question type and marks.
7. For MCQ:
   - options must contain exactly 4 strings.
   - answer must exactly match one option.
8. For Short and Long questions:
   - options must be null.
9. Return exactly these fields:

{{
    "text": "...",
    "subtopic": "...",
    "answer": "...",
    "options": null,
    "tags": []
}}
"""


def build_client() -> ChatGroq:
    api_key = os.environ.get("GROQ_API_KEY")
    model_name = os.environ.get("MODEL_NAME")

    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")

    if not model_name:
        raise RuntimeError("MODEL_NAME is not configured.")

    return ChatGroq(
        model=model_name,
        api_key=api_key,
        temperature=0.7,
        max_tokens=1000,
    )


def generate_question(
    old_question: Question,
    existing_questions: list[Question],
) -> Question:

    client = build_client()

    existing_text = "\n".join(f"- {question.text}" for question in existing_questions)

    prompt = PROMPT_TEMPLATE.format(
        topic=old_question.topic.value,
        difficulty=old_question.difficulty.value,
        qtype=old_question.qtype.value,
        marks=QTYPE_MARKS[old_question.qtype],
        existing_questions=existing_text,
    )

    response = client.invoke(prompt)

    text = response.content.strip()

    if text.startswith("```"):
        text = text.strip("`")

        if "\n" in text:
            text = text.split("\n", 1)[1]

    raw = json.loads(text)

    new_id = f"LLM-{old_question.topic.value[:3].upper()}-{id(raw)}"

    return Question(
        id=new_id,
        text=raw["text"],
        subject=old_question.subject,
        topic=old_question.topic,
        subtopic=raw.get("subtopic") or old_question.subtopic,
        difficulty=old_question.difficulty,
        qtype=old_question.qtype,
        marks=QTYPE_MARKS[old_question.qtype],
        options=raw.get("options"),
        answer=raw["answer"],
        tags=raw.get("tags", []),
        source=QuestionSource.LLM_ENRICHED,
    )
