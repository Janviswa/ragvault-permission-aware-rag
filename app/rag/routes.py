from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.rag.pipeline import retrieve_secure_context
from app.rag.llm import generate_answer
from app.security.audit import create_audit_log

router = APIRouter(prefix="/rag", tags=["RAG"])


class RAGQueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    limit: int = Field(default=5, ge=1, le=20)


class RAGSource(BaseModel):
    document_id: int
    title: str
    file_name: str
    chunk_index: int


class RAGQueryResponse(BaseModel):
    question: str
    answer: str
    sources: list[RAGSource]


@router.post("/query", response_model=RAGQueryResponse)
def query_rag(
    request: RAGQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    context, results = retrieve_secure_context(
        db=db,
        current_user=current_user,
        query=request.question,
        limit=request.limit,
    )

    answer = generate_answer(
        question=request.question,
        context=context,
    )
    create_audit_log(
        db=db,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        action="rag_query",
        resource_type="rag",
        resource_id=None,
        details=f"query_completed, authorized_source_count={len(results)}",
    )

    sources = [
        RAGSource(
            document_id=result.payload["document_id"],
            title=result.payload["title"],
            file_name=result.payload["file_name"],
            chunk_index=result.payload["chunk_index"],
        )
        for result in results
    ]

    return RAGQueryResponse(
        question=request.question,
        answer=answer,
        sources=sources,
    )