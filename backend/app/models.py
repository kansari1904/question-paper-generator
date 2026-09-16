from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class Topic(str, Enum):
    PHYSICS = "Physics"
    CHEMISTRY = "Chemistry"
    BIOLOGY = "Biology"


class Difficulty(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class QuestionType(str, Enum):
    MCQ = "MCQ"
    SHORT = "Short"
    LONG = "Long"


class QuestionSource(str, Enum):
    SEED = "seed"
    LLM_ENRICHED = "llm-enriched"


QTYPE_MARKS: dict[QuestionType, int] = {
    QuestionType.MCQ: 1,
    QuestionType.SHORT: 3,
    QuestionType.LONG: 5,
}


class Question(BaseModel):
    id: str
    text: str
    subject: str = "Science"
    topic: Topic
    subtopic: Optional[str] = None
    difficulty: Difficulty
    qtype: QuestionType
    marks: int
    options: Optional[list[str]] = None
    answer: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    source: QuestionSource = QuestionSource.SEED

    @model_validator(mode="after")
    def validate_question(self) -> "Question":
        expected_marks = QTYPE_MARKS[self.qtype]

        # Validate marks based on question type
        if self.marks != expected_marks:
            raise ValueError(
                f"{self.qtype.value} questions must have "
                f"{expected_marks} marks, got {self.marks}."
            )

        # MCQ validation
        if self.qtype == QuestionType.MCQ:
            if not self.options or len(self.options) != 4:
                raise ValueError("MCQ questions must contain exactly 4 options.")

            if not self.answer:
                raise ValueError("MCQ questions must contain an answer.")

        # Short / Long validation
        else:
            if self.options is not None:
                raise ValueError(
                    f"{self.qtype.value} questions must not contain options."
                )

            if not self.answer:
                raise ValueError(
                    f"{self.qtype.value} questions must contain an answer."
                )

        return self


class DifficultyMix(BaseModel):
    easy: float = Field(..., ge=0, le=100)
    medium: float = Field(..., ge=0, le=100)
    hard: float = Field(..., ge=0, le=100)

    @model_validator(mode="after")
    def sums_to_100(self) -> "DifficultyMix":
        total = self.easy + self.medium + self.hard

        if abs(total - 100) > 1e-6:
            raise ValueError(f"Difficulty percentages must sum to 100. Got {total}.")

        return self


class TopicWeightage(BaseModel):
    physics: float = Field(..., ge=0, le=100)
    chemistry: float = Field(..., ge=0, le=100)
    biology: float = Field(..., ge=0, le=100)

    @model_validator(mode="after")
    def sums_to_100(self) -> "TopicWeightage":
        total = self.physics + self.chemistry + self.biology

        if abs(total - 100) > 1e-6:
            raise ValueError(f"Topic percentages must sum to 100. Got {total}.")

        return self


class QuestionTypeMix(BaseModel):
    mcq: float = Field(..., ge=0, le=100)
    short: float = Field(..., ge=0, le=100)
    long: float = Field(..., ge=0, le=100)

    @model_validator(mode="after")
    def sums_to_100(self) -> "QuestionTypeMix":
        total = self.mcq + self.short + self.long

        if abs(total - 100) > 1e-6:
            raise ValueError(f"Question-type percentages must sum to 100. Got {total}.")

        return self


class PaperRequest(BaseModel):
    total_marks: int = Field(..., gt=0, le=500)
    difficulty_mix: DifficultyMix
    topic_weightage: TopicWeightage
    qtype_mix: QuestionTypeMix


class Deviation(BaseModel):
    dimension: str
    requested_pct: float
    actual_pct: float
    reason: str


class ConstraintReport(BaseModel):
    requested_total_marks: int
    actual_total_marks: int
    deviations: list[Deviation] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PaperSection(BaseModel):
    qtype: QuestionType
    instructions: str
    marks_subtotal: int
    question_ids: list[str]


class PaperResponse(BaseModel):
    paper_id: str
    total_marks: int
    sections: list[PaperSection]
    questions: list[Question]
    constraint_report: ConstraintReport


class SwapRequest(BaseModel):
    paper_id: str
    question_id: str


class SwapResponse(BaseModel):
    success: bool
    replaced_question_id: str
    new_question: Optional[Question] = None
    message: str
