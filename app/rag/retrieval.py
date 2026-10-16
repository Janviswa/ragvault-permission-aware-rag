from qdrant_client.models import Filter, FieldCondition, MatchAny

from app.rag.embeddings import generate_embedding
from app.rag.ingestion import COLLECTION_NAME
from app.vectorstore.qdrant import get_client


def search_documents(
    query: str,
    tenant_id: str,
    user_id: int,
    role: str,
    limit: int = 5,
):
    query_embedding = generate_embedding(query)

    must_conditions = [
        FieldCondition(
            key="tenant_id",
            match={"value": tenant_id},
        )
    ]

    # Admins can retrieve any document within their tenant.
    # Normal users must satisfy the Qdrant ACL filter.
    if role != "Admin":
        query_filter = Filter(
            must=must_conditions,
            should=[
                FieldCondition(
                    key="allowed_user_ids",
                    match=MatchAny(any=[user_id]),
                ),
                FieldCondition(
                    key="allowed_roles",
                    match=MatchAny(any=[role]),
                ),
            ],
        )
    else:
        query_filter = Filter(
            must=must_conditions,
        )

    return get_client().query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        query_filter=query_filter,
        limit=limit,
        with_payload=True,
    ).points