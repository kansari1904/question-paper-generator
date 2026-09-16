from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from app.models import PaperRequest, PaperResponse
from app.engine.composer import compose_paper
from app.engine.exact_solver import SolverError, solve_exact
from app.engine.resolver import build_constraint_report_from_selection
from app.engine.validator import ValidationError, compute_targets
from app.store import BANK, BANK_BY_ID, PAPERS


router = APIRouter(
    prefix="/paper",
    tags=["Paper"],
)


@router.post("/generate", response_model=PaperResponse)
def generate_paper(
    request: PaperRequest,
    seed: int = 42,
) -> PaperResponse:

    try:
        targets = compute_targets(request)

        selection = solve_exact(
            questions=BANK,
            total_marks=targets.total_marks,
            difficulty_targets=targets.difficulty_marks,
            topic_targets=targets.topic_marks,
            qtype_targets=targets.qtype_marks,
            seed=seed,
        )

    except ValidationError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except SolverError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    sections, ordered_questions = compose_paper(
        selection.selected_question_ids,
        BANK_BY_ID,
    )

    paper_id = str(uuid.uuid4())

    PAPERS[paper_id] = {
        "selection_ids": selection.selected_question_ids,
        "selection": selection,
        "request": request,
        "targets": targets,
        "seed": seed,
    }

    report = build_constraint_report_from_selection(
        request=request,
        targets=targets,
        selection=selection,
    )

    return PaperResponse(
        paper_id=paper_id,
        total_marks=selection.total_marks_achieved,
        sections=sections,
        questions=ordered_questions,
        constraint_report=report,
    )


@router.get("/{paper_id}", response_model=PaperResponse)
def get_paper(paper_id: str) -> PaperResponse:

    paper = PAPERS.get(paper_id)

    if paper is None:
        raise HTTPException(
            status_code=404,
            detail=f"Paper {paper_id} not found.",
        )

    selection = paper["selection"]

    sections, ordered_questions = compose_paper(
        paper["selection_ids"],
        BANK_BY_ID,
    )

    report = build_constraint_report_from_selection(
        request=paper["request"],
        targets=paper["targets"],
        selection=selection,
    )

    return PaperResponse(
        paper_id=paper_id,
        total_marks=selection.total_marks_achieved,
        sections=sections,
        questions=ordered_questions,
        constraint_report=report,
    )
