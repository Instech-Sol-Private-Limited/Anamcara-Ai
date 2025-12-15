# from database.supabase_db import get_client
# from typing import List, Dict, Optional
# from datetime import datetime
# import uuid
# supabase = get_client

# async def get_user_chat_history(user_id: str, limit: int = 10) -> List[Dict]:
#     """Get user's complete message history"""
#     try:
#         supabase = get_client()
        
#         result = supabase.table("chat_history")\
#             .select("messages")\
#             .eq("user_id", user_id)\
#             .execute()
        
#         if result.data and len(result.data) > 0:
#             # Return last 'limit' messages
#             messages = result.data[0].get("messages", [])
#             return messages[-limit:] if messages else []
#         return []
        
#     except Exception as e:
#         print(f"Error fetching chat history: {e}")
#         return []


# # async def save_chat_message(
# #     user_id: str,
# #     conversation_id: str,
# #     user_message: str,
# #     ai_message: str,
# #     user_type: str = "guest"
# # ) -> bool:
# #     """Append message to existing user row (or create new)"""
# #     try:
# #         supabase = get_client()
        
# #         # New message object
# #         new_message = {
# #             "role": "user",
# #             "content": user_message,
# #             "timestamp": datetime.utcnow().isoformat()
# #         }
        
# #         new_response = {
# #             "role": "assistant",
# #             "content": ai_message,
# #             "timestamp": datetime.utcnow().isoformat()
# #         }
        
# #         # Try to get existing row
# #         existing = supabase.table("chat_history")\
# #             .select("messages")\
# #             .eq("user_id", user_id)\
# #             .execute()
        
# #         if existing.data:
# #             # User exists - APPEND to messages
# #             current_messages = existing.data[0].get("messages", [])
# #             current_messages.extend([new_message, new_response])
            
# #             supabase.table("chat_history")\
# #                 .update({
# #                     "messages": current_messages,
# #                     "updated_at": datetime.utcnow().isoformat()
# #                 })\
# #                 .eq("user_id", user_id)\
# #                 .execute()
            
# #             print(f" Appended to user: {user_id}")
# #         else:
# #             # New user - CREATE row
# #             supabase.table("chat_history")\
# #                 .insert({
# #                     "user_id": user_id,
# #                     "conversation_id": conversation_id,
# #                     "messages": [new_message, new_response],
# #                     "user_type": user_type
# #                 })\
# #                 .execute()
            
# #             print(f" Created new entry for user: {user_id}")
        
# #         return True
        
# #     except Exception as e:
# #         print(f" Failed to save: {e}")
# #         return False
# async def save_chat_message(
#     user_id: str,
#     conversation_id: Optional[str],
#     user_message: str,
#     ai_message: str,
#     user_type: str = "guest"
# ):
#     try:
#         supabase = get_client()

#         # Create message objects
#         new_message = {
#             "role": "user",
#             "content": user_message,
#             "timestamp": datetime.utcnow().isoformat()
#         }

#         new_response = {
#             "role": "assistant",
#             "content": ai_message,
#             "timestamp": datetime.utcnow().isoformat()
#         }

#         # ----------------------------------------
#         # CASE 1: New conversation (conversation_id is None)
#         # ----------------------------------------
#         if not conversation_id:
#             conversation_id = str(uuid.uuid4())
#             supabase.table("chat_history").insert({
#                 "user_id": user_id,
#                 "conversation_id": conversation_id,
#                 "messages": [new_message, new_response],
#                 "user_type": user_type
#             }).execute()

#             print(" NEW conversation created:", conversation_id)
#             return conversation_id

#         # ----------------------------------------
#         # CASE 2: Append to existing conversation
#         # ----------------------------------------
#         existing = supabase.table("chat_history")\
#             .select("messages")\
#             .eq("user_id", user_id)\
#             .eq("conversation_id", conversation_id)\
#             .execute()

#         if existing.data:
#             current_messages = existing.data[0]["messages"]
#             current_messages.extend([new_message, new_response])

#             supabase.table("chat_history")\
#                 .update({"messages": current_messages})\
#                 .eq("user_id", user_id)\
#                 .eq("conversation_id", conversation_id)\
#                 .execute()

#             print(" Appended to conversation:", conversation_id)
#             return conversation_id

#         # ----------------------------------------
#         # FAILSAFE: If conversation_id provided but row didn't exist → create new
#         # ----------------------------------------
#         supabase.table("chat_history").insert({
#             "user_id": user_id,
#             "conversation_id": conversation_id,
#             "messages": [new_message, new_response],
#             "user_type": user_type
#         }).execute()

#         print(" Conversation id given but not found → new created")
#         return conversation_id

#     except Exception as e:
#         print(" Error:", e)
#         return None


# def format_chat_history_for_context(chat_history: List[Dict], max_messages: int = 5) -> str:
#     """Format for RAG context"""
#     if not chat_history:
#         return ""
    
#     recent = chat_history[-max_messages:]
    
#     formatted = "PREVIOUS CONVERSATION:\n"
#     for msg in recent:
#         role = msg.get("role", "user")
#         content = msg.get("content", "")
#         formatted += f"{role.upper()}: {content}\n"
    
#     return formatted

from database.supabase_db import get_client
from typing import List, Dict, Optional
from datetime import datetime
import uuid

async def get_user_chat_history(user_id: str, conversation_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
    """Get chat history for a user (optionally by conversation_id)"""
    try:
        supabase = get_client()
        query = supabase.table("chat_history").select("messages").eq("user_id", user_id)
        if conversation_id:
            query = query.eq("conversation_id", conversation_id)
        result = query.execute()

        if result.data and len(result.data) > 0:
            messages = result.data[0].get("messages", [])
            return messages[-limit:] if messages else []
        return []

    except Exception as e:
        print(f"Error fetching chat history: {e}")
        return []


async def save_chat_message(
    user_id: str,
    conversation_id: Optional[str],
    user_message: str,
    ai_message: str,
    user_type: str = "guest"
) -> str:
    """Save chat message: create new conversation if conversation_id is None"""
    try:
        supabase = get_client()

        # Prepare message objects
        new_message = {"role": "user", "content": user_message, "timestamp": datetime.utcnow().isoformat()}
        new_response = {"role": "assistant", "content": ai_message, "timestamp": datetime.utcnow().isoformat()}

        # New conversation
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            supabase.table("chat_history").insert({
                "user_id": user_id,
                "conversation_id": conversation_id,
                "messages": [new_message, new_response],
                "user_type": user_type,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).execute()
            print(" NEW conversation created:", conversation_id)
            return conversation_id

        # Append to existing conversation
        existing = supabase.table("chat_history")\
            .select("messages")\
            .eq("user_id", user_id)\
            .eq("conversation_id", conversation_id)\
            .execute()

        if existing.data:
            current_messages = existing.data[0].get("messages", [])
            current_messages.extend([new_message, new_response])
            supabase.table("chat_history")\
                .update({"messages": current_messages, "updated_at": datetime.utcnow().isoformat()})\
                .eq("user_id", user_id)\
                .eq("conversation_id", conversation_id)\
                .execute()
            print(" Appended to conversation:", conversation_id)
            return conversation_id

        # Fallback: conversation_id provided but row not found → create new
        supabase.table("chat_history").insert({
            "user_id": user_id,
            "conversation_id": conversation_id,
            "messages": [new_message, new_response],
            "user_type": user_type,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).execute()
        print(" Conversation id given but not found → new created")
        return conversation_id

    except Exception as e:
        print(" Error saving chat:", e)
        return str(uuid.uuid4())
    

def format_chat_history_for_context(chat_history: List[Dict], max_messages: int = 5) -> str:
    if not chat_history:
        return ""
    recent = chat_history[-max_messages:]
    formatted = "PREVIOUS CONVERSATION:\n"
    for msg in recent:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        formatted += f"{role.upper()}: {content}\n"
    return formatted


async def get_user_conversations(user_id: str) -> List[Dict]:
    """Fetch all conversations for a given user_id"""
    try:
        supabase = get_client()
        
        result = supabase.table("chat_history")\
            .select("conversation_id, messages")\
            .eq("user_id", user_id)\
            .execute()
        
        if result.data:
            # Format each row as {conversation_id, messages}
            conversations = []
            for row in result.data:
                conversations.append({
                    "conversation_id": row["conversation_id"],
                    "messages": row.get("messages", [])
                })
            return conversations
        
        return []
    
    except Exception as e:
        print(f"Error fetching conversations: {e}")
        return []