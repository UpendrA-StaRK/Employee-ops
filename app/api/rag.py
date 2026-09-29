"""RAG endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.rag import RagRequest, RagResponse
from app.services.retriever import retrieve_evidence
from app.services.generator import generate_answer

router = APIRouter(prefix="/rag", tags=["rag"])

@router.post(
    "/ask",
    response_model=RagResponse,
    summary="Ask a policy question"
)
def ask_policy_question(request: RagRequest, db: Session = Depends(get_db)) -> RagResponse:
    """
    Minimal grounded RAG path:
    1. Retrieve relevant evidence based on the question (now via Vector Search).
    2. Pass evidence to generator (with preserved identity).
    3. Return grounded answer and citations (or controlled no-answer).
    """
    evidence = retrieve_evidence(db, request.question, filters=request.filters)
    response = generate_answer(request.question, evidence)
    return response
