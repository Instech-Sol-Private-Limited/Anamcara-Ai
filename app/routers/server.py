from fastapi import APIRouter, HTTPException
from models.schemas import QueryRequest, QueryResponse, Message
from app.services.rag_engine import rag_query, warmup_models
from app.services.safety import check_safety
from datetime import datetime
import uuid
from database.supabase_db import get_client
from app.services.chat_services import (
    get_user_chat_history, 
    save_chat_message, 
    format_chat_history_for_context,
    get_user_conversations
)

router = APIRouter()

@router.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    # Safety check
    s = check_safety(request.query)
    if s["flag"]:
        return QueryResponse(message=s["response"], safety=s["type"])

    conversation_id = request.conversation_id or None  # None triggers new conversation

    chat_history_raw = []
    chat_context = ""

    if request.user_id and conversation_id:
        # Only fetch if existing conversation
        chat_history_raw = await get_user_chat_history(user_id=request.user_id, conversation_id=conversation_id, limit=10)
        chat_context = format_chat_history_for_context(chat_history_raw, max_messages=5)

    # Run RAG query
    answer = await rag_query(request.query, chat_context)
    is_error = answer.startswith("Error:")

    # Save message
    if request.user_id and not is_error:
        conversation_id = await save_chat_message(
            user_id=request.user_id,
            conversation_id=conversation_id,
            user_message=request.query,
            ai_message=answer,
            user_type=request.user_type
        )

    return QueryResponse(
        message=answer,
        safety="error" if is_error else "ok",
        conversation_id=conversation_id,
        chat_history=chat_history_raw
    )

@router.get("/api/history/{user_id}")
async def get_history(user_id: str, limit: int = 20):
    """Get user's complete chat history"""
    history = await get_user_chat_history(user_id, limit=limit)
    return {"user_id": user_id, "history": history, "count": len(history)}


@router.get("/api/conversation/{user_id}/{conversation_id}")
async def get_conversation(user_id: str, conversation_id: str):
    """Get specific conversation thread"""
    history = await get_user_chat_history(user_id, conversation_id=conversation_id)
    return {"conversation_id": conversation_id, "messages": history}

@router.get("/api/conversations/{user_id}")
async def get_conversations(user_id: str):
    """
    Get all conversations for a user_id.
    Returns format:
    [
        {
            "conversation_id": "xxxxxxxx",
            "messages": [...]
        }
    ]
    """
    conversations = await get_user_conversations(user_id)
    return {"user_id": user_id, "conversations": conversations, "count": len(conversations)}