from sqlalchemy.orm import Session

from app.rag.retrieval import search_documents
from app.rag.context import build_secure_context


def retrieve_secure_context(
    db: Session,
    current_user,
    query: str,
    limit: int = 5,
):
    results = search_documents(
        query=query,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        role=current_user.role,
        limit=limit,
    )

    secure_context, authorized_results = build_secure_context(
        db=db,
        current_user=current_user,
        results=results,
    )

    return secure_context, authorized_results