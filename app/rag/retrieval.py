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


def search_tenant_documents(query: str, tenant_id: str, limit: int = 5):
    """Tenant-scoped search that does NOT apply the user ACL filter.

    Only ever use this to decide *whether* something relevant exists that the
    caller cannot read. Never pass its payload text to the language model or
    return it to the client.
    """
    query_embedding = generate_embedding(query)
    return get_client().query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        query_filter=Filter(
            must=[FieldCondition(key="tenant_id", match={"value": tenant_id})]
        ),
        limit=limit,
        with_payload=True,
    ).points
