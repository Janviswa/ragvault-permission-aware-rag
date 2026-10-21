from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db import get_db
from app.models.chat import Chat, ChatMessage
from app.models.user import User

router = APIRouter(prefix="/chats", tags=["Chats"])


def _own_chat(db: Session, chat_id: int, user: User) -> Chat:
    chat = db.get(Chat, chat_id)
    # 404 (not 403) for someone else's chat so ids can't be probed.
    if not chat or chat.user_id != user.id:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.get("")
def list_chats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (
        db.query(Chat, func.count(ChatMessage.id))
        .outerjoin(ChatMessage, ChatMessage.chat_id == Chat.id)
        .filter(Chat.user_id == current_user.id)
        .group_by(Chat.id)
        .order_by(Chat.updated_at.desc())
        .limit(200)
        .all()
    )
    return [
        {
            "id": chat.id,
            "title": chat.title,
            "created_at": chat.created_at,
            "updated_at": chat.updated_at,
            "message_count": count,
        }
        for chat, count in rows
    ]


@router.get("/{chat_id}")
def get_chat(chat_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat = _own_chat(db, chat_id, current_user)
    return {
        "id": chat.id,
        "title": chat.title,
        "created_at": chat.created_at,
        "updated_at": chat.updated_at,
        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "sources": message.sources or [],
                "restricted": message.restricted,
                "created_at": message.created_at,
            }
            for message in chat.messages
        ],
    }


@router.delete("/{chat_id}")
def delete_chat(chat_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat = _own_chat(db, chat_id, current_user)
    db.delete(chat)
    db.commit()
    return {"message": "Chat deleted", "chat_id": chat_id}
