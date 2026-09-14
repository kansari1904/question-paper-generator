"""
models.py

Pydantic schema definitions for the Smart Question Paper Generator (Science).

These models are the single source of truth for data shapes used across
the engine (validator, feasibility, matrix_fit, selector, resolver,
composer, swap) and the FastAPI routes in main.py.

Design notes:
- Marks per question-type are fixed by assignment scope: MCQ = 1, Short = 3,
  Long = 5. This is enforced via QTYPE_MARKS and validated on Question
  creation so a malformed bank entry fails fast at load time, not at
  generation time.
- Topic/Difficulty/QuestionType are enums, not free strings, so the engine
  never has to defensively handle typos like "med" vs "Medium".
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

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


# Fixed marks per question type (assignment assumption, documented in README).
QTYPE_MARKS: dict[QuestionType, int] = {
    QuestionType.MCQ: 1,
    QuestionType.SHORT: 3,
    QuestionType.LONG: 5,
}


# ---------------------------------------------------------------------------
# Question bank entry
# ---------------------------------------------------------------------------

class Question(BaseModel):
    id: str = Field(..., description="Stable unique id, e.g. SCI-PHY-014")
    text: str
    subject: str = "Science"
    topic: Topic
    subtopic: Optional[str] = None
    difficulty: Difficulty
    qtype: QuestionType
    marks: int
    options: Optional[list[str]] = Field(
        default=None, description="Required for MCQ, must be null otherwise"
    )
    answer: str
    tags: list[str] = Field(default_factory=list)
    source: QuestionSource = QuestionSource.SEED

    @model_validator(mode="after")
    def _validate_marks_and_options(self) -> "Question":
        expected = QTYPE_MARKS[self.qtype]
        if self.marks != expected:
            raise ValueError(
                f"{self.id}: qtype {self.qtype} must have marks={expected}, "
                f"got {self.marks}"
            )
        if self.qtype == QuestionType.MCQ:
            if not self.options or len(self.options) != 4:
                raise ValueError(f"{self.id}: MCQ must have exactly 4 options")
        else:
            if self.options is not None:
                raise ValueError(
                    f"{self.id}: options must be null for non-MCQ questions"
                )
        return self


# ---------------------------------------------------------------------------
# Request: what the teacher submits
# ---------------------------------------------------------------------------

class DifficultyMix(BaseModel):
    easy: float = Field(..., ge=0, le=100)
    medium: float = Field(..., ge=0, le=100)
    hard: float = Field(..., ge=0, le=100)

    @model_validator(mode="after")
    def _sums_to_100(self) -> "DifficultyMix":
        total = self.easy + self.medium + self.hard
        if not (99.0 <= total <= 101.0):  # small rounding tolerance
            raise ValueError(f"Difficulty mix must sum to 100%, got {total}")
        return self


class TopicWeightage(BaseModel):
    physics: float = Field(..., ge=0, le=100)
    chemistry: float = Field(..., ge=0, le=100)
    biology: float = Field(..., ge=0, le=100)

    @model_validator(mode="after")
    def _sums_to_100(self) -> "TopicWeightage":
        total = self.physics + self.chemistry + self.biology
        if not (99.0 <= total <= 101.0):
            raise ValueError(f"Topic weightage must sum to 100%, got {total}")
        return self


class QuestionTypeMix(BaseModel):
    mcq: float = Field(..., ge=0, le=100)
    short: float = Field(..., ge=0, le=100)
    long: float = Field(..., ge=0, le=100)

    @model_validator(mode="after")
    def _sums_to_100(self) -> "QuestionTypeMix":
        total = self.mcq + self.short + self.long
        if not (99.0 <= total <= 101.0):
            raise ValueError(f"Question-type mix must sum to 100%, got {total}")
        return self


class PaperRequest(BaseModel):
    total_marks: int = Field(..., gt=0)
    difficulty_mix: DifficultyMix
    topic_weightage: TopicWeightage
    qtype_mix: QuestionTypeMix

    @field_validator("total_marks")
    @classmethod
    def _reasonable_total(cls, v: int) -> int:
        if v > 500:
            raise ValueError("total_marks unreasonably large for a single paper")
        return v


# ---------------------------------------------------------------------------
# Response: what the engine returns
# ---------------------------------------------------------------------------

class Deviation(BaseModel):
    """A single documented gap between what was requested and what was produced."""
    dimension: str  # e.g. "difficulty.easy", "topic.physics", "qtype.short"
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