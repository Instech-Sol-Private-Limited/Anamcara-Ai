# routes/chat_routes.py
from fastapi import APIRouter, HTTPException
from models.schemas import ChatMessage, ChatResponse
from app.services.openai_service import generate_chat_response
from models.supabase_helpers import serialize_doc
from database.supabase_db import get_client
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat(chat_message: ChatMessage):
    try:
        client = get_client()
        
        # Get persona details
        persona_result = client.table("personas").select("*").eq("id", chat_message.persona_id).execute()
        
        if not persona_result.data:
            raise HTTPException(status_code=404, detail="Persona not found")
        
        persona = persona_result.data[0]
        current_time = datetime.utcnow()
        
        # Get existing chat history for this thread
        chat_history_result = client.table("chat_messages").select("*").eq("thread_id", chat_message.thread_id).order("timestamp", desc=False).execute()
        
        # Prepare chat history for AI
        messages = []
        if chat_history_result.data:
            for msg in chat_history_result.data:
                role = "user" if msg["sender"] == "user" else "assistant"
                messages.append({"role": role, "content": msg["message"]})
        
        # Add current user message
        messages.append({"role": "user", "content": chat_message.message})
        
        # Generate AI response
        ai_response = await generate_chat_response(messages, persona)
        
        # Save user message
        user_message_data = {
            "thread_id": chat_message.thread_id,
            "persona_id": chat_message.persona_id,
            "user_id": persona["user_id"],
            "sender": "user",
            "message": chat_message.message,
            "timestamp": current_time.isoformat()
        }
        
        # Save AI response
        ai_message_data = {
            "thread_id": chat_message.thread_id,
            "persona_id": chat_message.persona_id,
            "user_id": persona["user_id"],
            "sender": "ai",
            "message": ai_response,
            "timestamp": current_time.isoformat()
        }
        
        # Insert both messages
        messages_to_insert = [user_message_data, ai_message_data]
        client.table("chat_messages").insert(messages_to_insert).execute()
        
        # Update persona's last interaction
        client.table("personas").update({
            "last_interaction": current_time.isoformat()
        }).eq("id", chat_message.persona_id).execute()
        
        return ChatResponse(
            response=ai_response,
            thread_id=chat_message.thread_id,
            persona_id=chat_message.persona_id,
            timestamp=current_time
        )
        
    except Exception as e:
        print(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@router.get("/history/{thread_id}")
async def get_chat_history(thread_id: str, limit: int = 50):
    try:
        client = get_client()
        
        # Get chat history for the thread
        result = client.table("chat_messages").select("*").eq("thread_id", thread_id).order("timestamp", desc=False).limit(limit).execute()
        
        if not result.data:
            return {"messages": []}
        
        return {"messages": [serialize_doc(msg) for msg in result.data]}
        
    except Exception as e:
        print(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get chat history: {str(e)}")

@router.get("/threads/{user_id}")
async def get_user_chat_threads(user_id: str):
    try:
        client = get_client()
        
        # Get all threads for the user with latest message info
        result = client.table("chat_messages").select("""
            thread_id,
            persona_id,
            personas!inner(name, gender),
            message,
            timestamp
        """).eq("user_id", user_id).order("timestamp", desc=True).execute()
        
        # Group by thread_id and get the latest message for each thread
        threads = {}
        for msg in result.data:
            thread_id = msg["thread_id"]
            if thread_id not in threads:
                threads[thread_id] = {
                    "thread_id": thread_id,
                    "persona_id": msg["persona_id"],
                    "persona_name": msg["personas"]["name"],
                    "persona_gender": msg["personas"]["gender"],
                    "last_message": msg["message"],
                    "last_timestamp": msg["timestamp"]
                }
        
        return {"threads": list(threads.values())}
        
    except Exception as e:
        print(f"Error getting chat threads: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get chat threads: {str(e)}")

@router.delete("/thread/{thread_id}")
async def delete_chat_thread(thread_id: str):
    try:
        client = get_client()
        
        # Delete all messages in the thread
        result = client.table("chat_messages").delete().eq("thread_id", thread_id).execute()
        
        return {"message": f"Chat thread deleted successfully"}
        
    except Exception as e:
        print(f"Error deleting chat thread: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete chat thread: {str(e)}")