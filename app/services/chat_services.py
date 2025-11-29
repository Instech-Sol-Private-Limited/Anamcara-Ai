from database.supabase_db import get_client
from typing import List, Dict, Optional
from datetime import datetime

supabase = get_client

async def get_user_chat_history(user_id: str, limit: int = 10) -> List[Dict]:
    """Get user's complete message history"""
    try:
        supabase = get_client()
        
        result = supabase.table("chat_history")\
            .select("messages")\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        
        if result.data and result.data.get("messages"):
            # Return last 'limit' messages
            return result.data["messages"][-limit:]
        return []
        
    except Exception as e:
        print(f"Error fetching chat history: {e}")
        return []


async def save_chat_message(
    user_id: str,
    conversation_id: str,
    user_message: str,
    ai_message: str,
    user_type: str = "guest"
) -> bool:
    """Append message to existing user row (or create new)"""
    try:
        supabase = get_client()
        
        # New message object
        new_message = {
            "role": "user",
            "content": user_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        new_response = {
            "role": "assistant",
            "content": ai_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Try to get existing row
        existing = supabase.table("chat_history")\
            .select("messages")\
            .eq("user_id", user_id)\
            .execute()
        
        if existing.data:
            # User exists - APPEND to messages
            current_messages = existing.data[0].get("messages", [])
            current_messages.extend([new_message, new_response])
            
            supabase.table("chat_history")\
                .update({
                    "messages": current_messages,
                    "updated_at": datetime.utcnow().isoformat()
                })\
                .eq("user_id", user_id)\
                .execute()
            
            print(f" Appended to user: {user_id}")
        else:
            # New user - CREATE row
            supabase.table("chat_history")\
                .insert({
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "messages": [new_message, new_response],
                    "user_type": user_type
                })\
                .execute()
            
            print(f" Created new entry for user: {user_id}")
        
        return True
        
    except Exception as e:
        print(f" Failed to save: {e}")
        return False


def format_chat_history_for_context(chat_history: List[Dict], max_messages: int = 5) -> str:
    """Format for RAG context"""
    if not chat_history:
        return ""
    
    recent = chat_history[-max_messages:]
    
    formatted = "PREVIOUS CONVERSATION:\n"
    for msg in recent:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        formatted += f"{role.upper()}: {content}\n"
    
    return formatted