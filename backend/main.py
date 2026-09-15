"""
main.py

FastAPI application entry point.

This module is intentionally thin: it parses requests, calls the engine
pipeline in order, and shapes responses. No business logic lives here --
every decision (validation rules, feasibility checks, matrix fitting,
selection, conflict resolution, composition, swapping) lives in engine/
and is independently unit tested there. If you find yourself writing an
if/for loop with real logic in a route handler below, that logic belongs
in engine/ instead.

Run with: uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import json
import pathlib
import uuid
from collections import defaultdict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    PaperRequest,
    PaperResponse,
    Question,
    SwapRequest,
    SwapResponse,
)
from app.engine.validator import ValidationError, Targets, compute_targets

from app.engine.feasibility import check_feasibility

from app.engine.matrix_fit import fit_matrix

from app.engine.selector import SelectionResult, select_questions

from app.engine.resolver import build_constraint_report

from app.engine.composer import compose_paper
from app.engine.swap import swap_question

app = FastAPI(
    title="Smart Question Paper Generator (Science)",
    version="0.1.0",
)

# CORS for the React dev server. Tighten allow_origins before deploying.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BANK_PATH = pathlib.Path(__file__).parent/"app"/"data"/"question_bank.json"


def _load_bank() -> list[Question]:
    with open(BANK_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    return [Question(**q) for q in raw]


# Loaded once at startup, not per-request -- the bank is small enough to
# live entirely in memory, and re-reading the file on every call would be
# wasted I/O for no benefit.
BANK: list[Question] = _load_bank()
BANK_BY_ID: dict[str, Question] = {q.id: q for q in BANK}

# In-memory paper store, keyed by paper_id. A real deployment would use a
# database or cache keyed by session/user; in-memory is sufficient for this
# assignment's scope and keeps the demo dependency-free. Restarting the
# server clears all generated papers.
PAPERS: dict[str, dict] = {}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "bank_size": len(BANK)}


@app.post("/generate", response_model=PaperResponse)
def generate_paper(request: PaperRequest, seed: int = 42) -> PaperResponse:
    """Run the full pipeline (Stages 0-6) and return a generated paper
    along with its constraint report.

    `seed` controls which valid paper is produced when multiple papers
    could satisfy the same request -- pass a new seed to regenerate a
    different paper for the same constraints, or omit it to reuse the
    default.
    """
    try:
        targets = compute_targets(request)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    feasibility = check_feasibility(targets, BANK)
    matrix = fit_matrix(targets, feasibility.supply_by_cell)
    selection = select_questions(matrix, BANK, targets.total_marks, seed=seed)
    report = build_constraint_report(
        request, targets, BANK_BY_ID, feasibility, matrix, selection
    )
    sections, ordered_questions = compose_paper(
        selection.selected_question_ids, BANK_BY_ID
    )

    paper_id = str(uuid.uuid4())
    PAPERS[paper_id] = {
        "selection_ids": selection.selected_question_ids,
        "targets": targets,
        "seed": seed,
    }

    return PaperResponse(
        paper_id=paper_id,
        total_marks=selection.total_marks_achieved,
        sections=sections,
        questions=ordered_questions,
        constraint_report=report,
    )


@app.post("/swap", response_model=SwapResponse)
def swap_paper_question(request: SwapRequest) -> SwapResponse:
    """Replace a single question in an existing paper without re-running
    the full generation pipeline (Stage 7 -- see engine/swap.py)."""
    paper = PAPERS.get(request.paper_id)
    if paper is None:
        raise HTTPException(
            status_code=404, detail=f"Paper {request.paper_id} not found."
        )

    result = swap_question(paper["selection_ids"], request.question_id, BANK_BY_ID)
    if result.success:
        paper["selection_ids"] = result.updated_selection_ids

    return SwapResponse(
        success=result.success,
        replaced_question_id=result.replaced_question_id,
        new_question=result.new_question,
        message=result.message,
    )


@app.get("/paper/{paper_id}", response_model=PaperResponse)
def get_paper(paper_id: str) -> PaperResponse:
    """Fetch a previously generated paper, recomposed and with a fresh
    constraint report -- needed because a swap since generation may have
    changed the selection."""
    paper = PAPERS.get(paper_id)
    if paper is None:
        raise HTTPException(status_code=404, detail=f"Paper {paper_id} not found.")

    targets: Targets = paper["targets"]
    selection_ids: list[str] = paper["selection_ids"]

    selection = _selection_result_from_ids(selection_ids, BANK_BY_ID)
    # Feasibility/matrix are not recomputed after a swap -- a swap only
    # ever substitutes within the same qtype (see engine/swap.py), so it
    # cannot introduce a new feasibility gap that generation didn't
    # already know about. An empty feasibility/matrix pair here simply
    # means "no additional bank-limit warnings beyond what swap already
    # reported," which is accurate.
    empty_feasibility = check_feasibility(targets, [])
    empty_matrix = fit_matrix(targets, {})
    report = build_constraint_report(
        None, targets, BANK_BY_ID, empty_feasibility, empty_matrix, selection
    )
    sections, ordered_questions = compose_paper(selection_ids, BANK_BY_ID)

    return PaperResponse(
        paper_id=paper_id,
        total_marks=selection.total_marks_achieved,
        sections=sections,
        questions=ordered_questions,
        constraint_report=report,
    )


def _selection_result_from_ids(
    selection_ids: list[str], bank_by_id: dict[str, Question]
) -> SelectionResult:
    """Rebuild a SelectionResult purely from a current id list, for
    re-reporting after a swap (no new shortfalls/substitutions to add --
    swap.py already resolved or reported those at swap time)."""
    achieved: dict = defaultdict(int)
    for qid in selection_ids:
        q = bank_by_id[qid]
        cell = (q.topic.value, q.difficulty.value, q.qtype.value)
        achieved[cell] += q.marks

    return SelectionResult(
        selected_question_ids=selection_ids,
        achieved_marks_by_cell=dict(achieved),
        total_marks_achieved=sum(bank_by_id[qid].marks for qid in selection_ids),
        unmet_marks_by_cell={},
        substitutions=[],
    )
