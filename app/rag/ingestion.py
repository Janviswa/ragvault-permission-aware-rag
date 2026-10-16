from uuid import uuid5, NAMESPACE_URL
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    PointStruct,
    VectorParams,
)
from sqlalchemy.orm import Session
from app.models.document import Document
from app.models.document_permission import DocumentPermission
from app.rag.chunking import chunk_text
from app.rag.embeddings import generate_embeddings
from app.vectorstore.qdrant import get_client
from datetime import datetime
from app.models.temporary_access import TemporaryAccess

COLLECTION_NAME = "ragvault_documents"
VECTOR_SIZE = 384

def ensure_collection() -> None:
    client = get_client()
    names = {c.name for c in client.get_collections().collections}
    if COLLECTION_NAME not in names:
        client.create_collection(collection_name=COLLECTION_NAME, vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE))

def ingest_document(db: Session, document: Document) -> int:
    if not document.content:
        return 0
    ensure_collection()
    chunks = chunk_text(document.content)
    if not chunks:
        return 0
    permissions = db.query(DocumentPermission).filter(DocumentPermission.document_id == document.id, DocumentPermission.permission == "read").all()
    allowed_user_ids = [p.user_id for p in permissions if p.user_id is not None]
    allowed_roles = [p.role for p in permissions if p.role is not None]
    embeddings = generate_embeddings(chunks)
    points = []
    for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        point_id = str(uuid5(NAMESPACE_URL, f"ragvault:{document.id}:{index}"))
        payload = {"document_id": document.id, "chunk_index": index, "tenant_id": document.tenant_id, "classification": document.classification, "title": document.title, "file_name": document.file_name, "text": chunk, "allowed_user_ids": allowed_user_ids, "allowed_roles": allowed_roles}
        points.append(PointStruct(id=point_id, vector=embedding, payload=payload))
    get_client().upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)

def sync_document_permissions(db: Session, document_id: int) -> None:
    """
    Update ACL metadata for all existing Qdrant chunks
    belonging to a document without regenerating embeddings.
    """

    ensure_collection()

    permissions = (
        db.query(DocumentPermission)
        .filter(
            DocumentPermission.document_id == document_id,
            DocumentPermission.permission == "read",
        )
        .all()
    )

    temporary_accesses = (
        db.query(TemporaryAccess)
        .filter(
            TemporaryAccess.document_id == document_id,
            TemporaryAccess.expires_at > datetime.utcnow(),
        )
        .all()
    )

    allowed_user_ids = list(dict.fromkeys(
        [
            permission.user_id
            for permission in permissions
            if permission.user_id is not None
        ]
        + [
            access.user_id
            for access in temporary_accesses
            if access.user_id is not None
        ]
    ))

    allowed_roles = [
        permission.role
        for permission in permissions
        if permission.role is not None
    ]

    client = get_client()

    client.set_payload(
        collection_name=COLLECTION_NAME,
        payload={
            "allowed_user_ids": allowed_user_ids,
            "allowed_roles": allowed_roles,
        },
        points=Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match={"value": document_id},
                )
            ]
        ),
    )


def delete_document_vectors(document_id: int) -> None:
    ensure_collection()
    get_client().delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match={"value": document_id},
                )
            ]
        ),
    )