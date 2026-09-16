from pathlib import Path
import json

from app.models import Question


BASE_DIR = Path(__file__).resolve().parent
BANK_PATH = BASE_DIR / "data" / "question_bank.json"


def load_question_bank() -> list[Question]:
    with open(BANK_PATH, encoding="utf-8") as file:
        raw_questions = json.load(file)

    return [Question(**question) for question in raw_questions]


BANK = load_question_bank()
BANK_BY_ID = {question.id: question for question in BANK}

PAPERS = {}
