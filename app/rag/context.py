from app.rag.security import verify_retrieved_documents


def build_secure_context(db, current_user, results):
    authorized_results = verify_retrieved_documents(
        db,
        current_user,
        results,
    )

    if not authorized_results:
        return "", []

    parts = []

    for result in authorized_results:
        payload = result.payload or {}
        text = payload.get("text", "")

        if text:
            parts.append(
                f"Document: {payload.get('title', 'Unknown Document')}\n"
                f"Content:\n{text}"
            )

    secure_context = "\n\n---\n\n".join(parts)

    return secure_context, authorized_results