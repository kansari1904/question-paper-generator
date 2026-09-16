from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models import SwapRequest, SwapResponse
from app.engine.swap import swap_question
from app.engine.exact_solver import build_selection_result
from app.store import BANK_BY_ID, PAPERS


router = APIRouter(
    prefix="/paper",
    tags=["Swap"],
)


@router.post("/swap", response_model=SwapResponse)
def swap_paper_question(
    request: SwapRequest,
) -> SwapResponse:

    paper = PAPERS.get(request.paper_id)

    if paper is None:
        raise HTTPException(
            status_code=404,
            detail=f"Paper {request.paper_id} not found.",
        )

    result = swap_question(
        current_selection_ids=paper["selection_ids"],
        question_id_to_replace=request.question_id,
        bank_by_id=BANK_BY_ID,
    )

    if result.success:
        paper["selection_ids"] = result.updated_selection_ids

        selected_questions = [BANK_BY_ID[qid] for qid in result.updated_selection_ids]

        paper["selection"] = build_selection_result(selected_questions)

    return SwapResponse(
        success=result.success,
        replaced_question_id=result.replaced_question_id,
        new_question=result.new_question,
        message=result.message,
    )
