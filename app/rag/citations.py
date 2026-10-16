def build_sources(results):
    """Convert authorized Qdrant results into source metadata for API responses."""
    sources = []
    for result in results:
        payload = result.payload or {}
        sources.append({
            "document_id": payload.get("document_id"),
            "title": payload.get("title"),
            "file_name": payload.get("file_name"),
            "chunk_index": payload.get("chunk_index"),
            "score": result.score,
        })
    return sources
