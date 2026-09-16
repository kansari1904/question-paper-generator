"""
scripts/enrich_bank.py

Offline LLM enrichment of the seed question bank.

This is NOT called at runtime by the API -- it's a standalone script a
developer runs manually, before deploying, to expand question_bank.json
from the hand-written seed questions toward a larger pool with more
phrasing and subtopic variety. The constraint engine (Stages 0-7) never
calls an LLM; this script is the one deliberate exception, and it only
ever touches the data file, never a live request.

Model provider: Groq, via LangChain's ChatGroq wrapper. Using the
LangChain wrapper rather than the raw Groq SDK keeps this script on the
same abstraction the rest of the project already uses (LangChain/
LangGraph), and means swapping providers later (Groq -> Anthropic -> a
local model) is a one-line change to the client construction, not a
rewrite of call_model()'s parsing logic.

Usage:
    # .env (in backend/, or wherever you run this from):
    #   GROQ_API_KEY=gsk_...
    #   MODEL_NAME=llama-3.3-70b-versatile   # or whichever Groq model you use

    pip install langchain-groq python-dotenv --break-system-packages
    python scripts/enrich_bank.py --per-question 2

    # Test against just the first 3 seed questions before running the
    # full bank (recommended -- see main() for --limit):
    python scripts/enrich_bank.py --per-question 2 --limit 3 --out /tmp/test_bank.json

For each seed question, the model is asked to generate N new questions
that share the same topic, difficulty, qtype, and marks -- so the bank
gains real inventory in the same cell rather than skewing the overall
distribution -- but differ in phrasing and, where sensible, subtopic.

Every generated item is validated against models.Question before being
added. Anything that fails validation (wrong MCQ option count, a marks
mismatch, a missing answer) is dropped and logged to stderr rather than
silently included -- an unvalidated bank entry would be a much harder bug
to trace than a script that logs what it skipped.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.models import Question, QuestionSource, QTYPE_MARKS  # noqa: E402

try:
    from langchain_groq import ChatGroq
except ImportError:
    ChatGroq = None

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

TOPIC_PREFIX = {"Physics": "SCI-PHY", "Chemistry": "SCI-CHE", "Biology": "SCI-BIO"}

PROMPT_TEMPLATE = """You are helping expand a school Science question bank for a \
question-paper generator.

Given this seed question, generate {n} new questions covering the SAME topic \
({topic}), SAME difficulty ({difficulty}), and SAME question type ({qtype}) -- \
but with different phrasing and, where sensible, a different subtopic within \
{topic}.

Seed question:
{seed_text}

Rules:
- Return ONLY a JSON array, no prose, no markdown code fences.
- Each item must have exactly these fields: text, subtopic, answer, options, tags.
- Do NOT include id, subject, topic, difficulty, qtype, or marks -- those are \
fixed by the caller from the seed question.
- options must be null unless qtype is MCQ, in which case it must be an array \
of exactly 4 strings, and answer must equal one of them verbatim.
- tags must be an array (can be empty).
- Keep questions at a class 9-10 CBSE Science level and factually accurate.
"""


def build_prompt(seed: Question, n: int) -> str:
    return PROMPT_TEMPLATE.format(
        n=n,
        topic=seed.topic.value,
        difficulty=seed.difficulty.value,
        qtype=seed.qtype.value,
        seed_text=seed.text,
    )


def build_client() -> "ChatGroq":
    """Construct the LangChain Groq client from env vars. Kept separate
    from main() so tests/other callers can swap in a different client
    without touching argument parsing."""
    if ChatGroq is None:
        sys.exit(
            "Missing dependency: pip install langchain-groq --break-system-packages"
        )
    api_key = os.environ.get("GROQ_API_KEY")
    model_name = os.environ.get("MODEL_NAME")
    if not api_key:
        sys.exit("Set GROQ_API_KEY (in your .env or shell) before running this script.")
    if not model_name:
        sys.exit("Set MODEL_NAME (in your .env or shell) before running this script.")
    return ChatGroq(model=model_name, api_key=api_key, temperature=0.7, max_tokens=1500)


def call_model(client: "ChatGroq", prompt: str) -> list[dict]:
    """Call the model and parse the JSON array response. Raises
    json.JSONDecodeError on a parse failure, or whatever LangChain/Groq
    raises on a network/API failure -- callers catch and skip rather than
    letting one bad response abort the whole run."""
    response = client.invoke(prompt)
    text = response.content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if "\n" in text:
            text = text.split("\n", 1)[1]
    return json.loads(text)


def build_question(seed: Question, raw: dict, new_id: str) -> Question:
    """Turn one raw model-generated item into a validated Question, fixing
    topic/difficulty/qtype/marks/subject/source from the seed rather than
    trusting the model to echo them back correctly."""
    return Question(
        id=new_id,
        text=raw["text"],
        subject=seed.subject,
        topic=seed.topic,
        subtopic=raw.get("subtopic") or seed.subtopic,
        difficulty=seed.difficulty,
        qtype=seed.qtype,
        marks=QTYPE_MARKS[seed.qtype],
        options=raw.get("options"),
        answer=raw["answer"],
        tags=raw.get("tags", []),
        source=QuestionSource.LLM_ENRICHED,
    )


def next_id_for(topic_prefix: str, existing_ids: set[str]) -> str:
    n = 1
    while True:
        candidate = f"{topic_prefix}-{n:03d}"
        if candidate not in existing_ids:
            return candidate
        n += 1


def enrich(
    seed_questions: list[Question],
    per_question: int,
    limit: int | None,
    call_model_fn=call_model,
    client=None,
) -> list[Question]:
    """Pure-ish orchestration: given seed questions and a model-calling
    function, returns seed + enriched questions. call_model_fn and client
    are injectable so this function is testable without a real API call
    or a real Groq client."""
    existing_ids = {q.id for q in seed_questions}
    enriched: list[Question] = []
    targets = seed_questions if limit is None else seed_questions[:limit]

    for seed in targets:
        prompt = build_prompt(seed, per_question)
        try:
            raw_items = call_model_fn(client, prompt)
        except (json.JSONDecodeError, KeyError) as e:
            print(
                f"[skip] {seed.id}: model response could not be parsed ({e})",
                file=sys.stderr,
            )
            continue
        except Exception as e:  # network/API errors from Groq -- keep the run going
            print(f"[skip] {seed.id}: model call failed ({e})", file=sys.stderr)
            continue

        for raw in raw_items:
            prefix = TOPIC_PREFIX[seed.topic.value]
            new_id = next_id_for(prefix, existing_ids)
            try:
                q = build_question(seed, raw, new_id)
            except (ValidationError, KeyError) as e:
                print(
                    f"[drop] generated from {seed.id} failed validation: {e}",
                    file=sys.stderr,
                )
                continue
            existing_ids.add(new_id)
            enriched.append(q)

    return seed_questions + enriched


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bank", default="data/question_bank.json")
    parser.add_argument("--out", default=None, help="defaults to overwriting --bank")
    parser.add_argument("--per-question", type=int, default=2)
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="only enrich the first N seed questions -- use this for a cheap test run first",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="path to a .env file to load GROQ_API_KEY/MODEL_NAME from (default: .env in the cwd)",
    )
    args = parser.parse_args()

    if load_dotenv is not None:
        load_dotenv(args.env_file)
    elif not os.environ.get("GROQ_API_KEY"):
        print(
            "python-dotenv not installed and GROQ_API_KEY not already set in the "
            "environment -- install python-dotenv or export the vars manually.",
            file=sys.stderr,
        )

    client = build_client()

    bank_path = Path(args.bank)
    out_path = Path(args.out) if args.out else bank_path

    with open(bank_path, encoding="utf-8") as f:
        seed_questions = [Question(**q) for q in json.load(f)]

    full_bank = enrich(
        seed_questions, args.per_question, args.limit, call_model, client
    )

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            [json.loads(q.model_dump_json()) for q in full_bank],
            f,
            indent=2,
            ensure_ascii=False,
        )

    seed_count = sum(1 for q in full_bank if q.source == QuestionSource.SEED)
    enriched_count = len(full_bank) - seed_count
    print(
        f"Wrote {len(full_bank)} questions to {out_path} "
        f"({seed_count} seed, {enriched_count} llm-enriched)."
    )


if __name__ == "__main__":
    main()
