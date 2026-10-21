import asyncio
import json
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import SessionLocal, get_db
from app.auth.dependencies import get_current_user
from app.models.chat import Chat, ChatMessage
from app.models.user import User
from app.rag.pipeline import retrieve_secure_context
from app.rag.restricted import find_restricted_match
from app.rag.llm import generate_answer, stream_answer
from app.security.audit import create_audit_log

log = logging.getLogger("ragvault.rag")
router = APIRouter(prefix="/rag", tags=["RAG"])


class RAGQueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    limit: int = Field(default=5, ge=1, le=20)
    chat_id: int | None = Field(default=None, gt=0)


class RAGSource(BaseModel):
    document_id: int
    title: str
    file_name: str
    chunk_index: int


class RestrictedDocument(BaseModel):
    document_id: int
    title: str
    file_name: str
    classification: str
    required_roles: list[str]
    your_role: str


class RAGQueryResponse(BaseModel):
    question: str
    answer: str
    sources: list[RAGSource]
    chat_id: int
    restricted: RestrictedDocument | None = None


@router.post("/query", response_model=RAGQueryResponse)
def query_rag(
    request: RAGQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = None
    if request.chat_id is not None:
        chat = db.get(Chat, request.chat_id)
        # Report "not found" for other people's chats too, so ids can't be probed.
        if not chat or chat.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Chat not found")

    context, results = retrieve_secure_context(
        db=db,
        current_user=current_user,
        query=request.question,
        limit=request.limit,
    )

    restricted = find_restricted_match(db, current_user, request.question, results)

    if restricted:
        # Never hand anything to the model when a better match is off-limits.
        results = []
        answer = (
            "I can't answer that from the documents you can open. "
            f"The most relevant document, \u201c{restricted['title']}\u201d, "
            "needs a role you don't have."
        )
    else:
        try:
            answer = generate_answer(question=request.question, context=context)
        except Exception:
            log.exception("llm_generation_failed")
            raise HTTPException(
                status_code=502,
                detail="The assistant is unavailable right now. Check the language model configuration and try again.",
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

    now = datetime.utcnow()
    if chat is None:
        chat = Chat(
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            title=request.question.strip()[:60],
            created_at=now,
            updated_at=now,
        )
        db.add(chat)
        db.flush()
    chat.updated_at = now
    db.add(ChatMessage(chat_id=chat.id, role="user", content=request.question, created_at=now))
    db.add(
        ChatMessage(
            chat_id=chat.id,
            role="assistant",
            content=answer,
            sources=[source.model_dump() for source in sources],
            restricted=restricted,
            created_at=now,
        )
    )
    db.commit()

    document_ids = ",".join(str(i) for i in sorted({s.document_id for s in sources}))
    create_audit_log(
        db=db,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        action="rag_query",
        resource_type="rag",
        resource_id=None,
        details=(
            f"query_completed, authorized_source_count={len(results)}"
            + (f", documents={document_ids}" if document_ids else "")
            + (f", restricted_document={restricted['document_id']}" if restricted else "")
        ),
    )

    return RAGQueryResponse(
        question=request.question,
        answer=answer,
        sources=sources,
        chat_id=chat.id,
        restricted=restricted,
    )


# --------------------------------------------------------------------------- #
# Streaming variant: the answer arrives piece by piece (Server-Sent Events).
#
#   event: meta   {chat_id, sources, restricted}   sent first, so sources show immediately
#   event: token  {t}                              one per piece of the answer
#   event: done   {answer}                         the full, final answer text
#   event: error  {message}                        the model failed part-way
#
# If the client disconnects (the Stop button) the partial answer is saved with a
# "stopped" marker so chat history matches what the person saw.
# --------------------------------------------------------------------------- #

STOPPED_MARK = "\n\n*— stopped —*"
EMPTY_ANSWER = "I could not find that information in the authorized documents."


@dataclass
class StreamTurn:
    chat_id: int
    user_message_id: int
    new_chat: bool
    user_id: int
    tenant_id: str
    question: str
    context: str
    sources: list[dict] = field(default_factory=list)
    restricted: dict | None = None

    def meta(self) -> dict:
        return {"chat_id": self.chat_id, "sources": self.sources, "restricted": self.restricted}

    def audit_details(self) -> str:
        ids = ",".join(str(i) for i in sorted({s["document_id"] for s in self.sources}))
        return (
            f"query_completed, authorized_source_count={len(self.sources)}"
            + (f", documents={ids}" if ids else "")
            + (f", restricted_document={self.restricted['document_id']}" if self.restricted else "")
        )


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


def _persist_answer(turn: StreamTurn, text: str) -> None:
    """Save the assistant's message. Uses its own session: the request's one may be closed already."""
    now = datetime.utcnow()
    with SessionLocal() as db:
        chat = db.get(Chat, turn.chat_id)
        if chat is None:  # the person deleted the chat while it was streaming
            return
        chat.updated_at = now
        db.add(
            ChatMessage(
                chat_id=turn.chat_id,
                role="assistant",
                content=text,
                sources=turn.sources,
                restricted=turn.restricted,
                created_at=now,
            )
        )
        db.commit()
        create_audit_log(
            db=db,
            user_id=turn.user_id,
            tenant_id=turn.tenant_id,
            action="rag_query",
            resource_type="rag",
            resource_id=None,
            details=turn.audit_details(),
        )


def _rollback_turn(turn: StreamTurn) -> None:
    """The model failed before producing anything: leave no trace of the question."""
    with SessionLocal() as db:
        message = db.get(ChatMessage, turn.user_message_id)
        if message is not None:
            db.delete(message)
        if turn.new_chat:
            chat = db.get(Chat, turn.chat_id)
            if chat is not None:
                db.delete(chat)
        db.commit()


async def restricted_events(turn: StreamTurn, answer: str):
    try:
        yield _sse("meta", turn.meta())
        yield _sse("done", {"answer": answer})
    finally:
        _persist_answer(turn, answer)


async def answer_events(turn: StreamTurn):
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()
    stop = threading.Event()

    def put(item) -> None:
        try:
            loop.call_soon_threadsafe(queue.put_nowait, item)
        except RuntimeError:  # event loop already closed
            pass

    def worker() -> None:
        try:
            for piece in stream_answer(question=turn.question, context=turn.context):
                if stop.is_set():
                    break
                put(("token", piece))
            put(("end", None))
        except Exception as exc:  # noqa: BLE001 - reported to the client below
            put(("error", exc))

    threading.Thread(target=worker, daemon=True, name="rag-stream").start()

    parts: list[str] = []
    completed = False
    failure: Exception | None = None
    try:
        yield _sse("meta", turn.meta())
        while True:
            kind, payload = await queue.get()
            if kind == "token":
                if not parts:
                    payload = payload.lstrip()
                if not payload:
                    continue
                parts.append(payload)
                yield _sse("token", {"t": payload})
            elif kind == "end":
                completed = True
                break
            else:
                failure = payload
                break
        if failure is not None:
            log.error("llm_stream_failed", exc_info=failure)
            yield _sse("error", {"message": "The assistant is unavailable right now. Check the language model configuration and try again."})
        else:
            yield _sse("done", {"answer": "".join(parts) or EMPTY_ANSWER})
    finally:
        # Runs on normal completion, on error, and when the client disconnects (Stop).
        # Synchronous on purpose: a cancelled task can't be relied on to await anything here.
        stop.set()
        text = "".join(parts)
        if completed:
            _persist_answer(turn, text or EMPTY_ANSWER)
        elif failure is not None and not parts:
            _rollback_turn(turn)
        else:
            _persist_answer(turn, (text + STOPPED_MARK) if text else STOPPED_MARK.strip())


@router.post("/query/stream")
def query_rag_stream(
    request: RAGQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = None
    if request.chat_id is not None:
        chat = db.get(Chat, request.chat_id)
        if not chat or chat.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Chat not found")

    context, results = retrieve_secure_context(
        db=db,
        current_user=current_user,
        query=request.question,
        limit=request.limit,
    )
    restricted = find_restricted_match(db, current_user, request.question, results)
    restricted_answer = None
    if restricted:
        results = []  # never hand anything to the model when a better match is off-limits
        restricted_answer = (
            "I can't answer that from the documents you can open. "
            f"The most relevant document, \u201c{restricted['title']}\u201d, "
            "needs a role you don't have."
        )

    sources = [
        {
            "document_id": r.payload["document_id"],
            "title": r.payload["title"],
            "file_name": r.payload["file_name"],
            "chunk_index": r.payload["chunk_index"],
        }
        for r in results
    ]

    # Save the question now so the client gets a chat id up front.
    now = datetime.utcnow()
    new_chat = chat is None
    if chat is None:
        chat = Chat(
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            title=request.question.strip()[:60],
            created_at=now,
            updated_at=now,
        )
        db.add(chat)
        db.flush()
    chat.updated_at = now
    user_message = ChatMessage(chat_id=chat.id, role="user", content=request.question, created_at=now)
    db.add(user_message)
    db.commit()

    turn = StreamTurn(
        chat_id=chat.id,
        user_message_id=user_message.id,
        new_chat=new_chat,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        question=request.question,
        context="" if restricted else context,
        sources=sources,
        restricted=restricted,
    )
    events = restricted_events(turn, restricted_answer) if restricted else answer_events(turn)
    return StreamingResponse(
        events,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
