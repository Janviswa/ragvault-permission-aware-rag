from fastapi import HTTPException
from app.models.document import Document
from app.security.acl import check_document_access


def verify_retrieved_documents(
    db,
    current_user,
    results,
):
    authorized_results = []

    for result in results:
        payload = result.payload or {}
        document_id = payload.get("document_id")

        if not document_id:
            continue

        document = db.get(Document, document_id)

        if not document:
            continue

        try:
            check_document_access(
                db,
                current_user,
                document,
            )
        except HTTPException:
            continue

        authorized_results.append(result)

    return authorized_results