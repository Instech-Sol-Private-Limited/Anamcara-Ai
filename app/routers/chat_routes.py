from fastapi import APIRouter, HTTPException
from models.schemas import ChatMessage, ChatResponse
from app.services.openai_service import generate_chat_response
from models.mongo_helpers import serialize_doc
from datetime import datetime
from bson import ObjectId

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat(chat_message: ChatMessage):
    from database.mongodb import db
    persona = await db.personas.find_one({"_id": ObjectId(chat_message.persona_id)})
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    # Find the user's chat document
    user_chat = await db.chats.find_one({"user_id": persona["user_id"]})

    user_msg = {
        "sender": "user",
        "message": chat_message.message,
        "timestamp": datetime.utcnow()
    }

    ai_response = None
    thread_found = False

    if user_chat:
        for thread in user_chat["threads"]:
            if thread["thread_id"] == chat_message.thread_id:
                # Prepare chat history for AI
                messages = [
                    {"role": "user" if m["sender"] == "user" else "assistant", "content": m["message"]}
                    for m in thread["messages"]
                ]
                messages.append({"role": "user", "content": chat_message.message})
                ai_response = await generate_chat_response(messages, persona)

                # Append both user and AI messages
                thread["messages"].append(user_msg)
                thread["messages"].append({
                    "sender": "ai",
                    "message": ai_response,
                    "timestamp": datetime.utcnow()
                })
                thread_found = True
                break

    if not user_chat:
        # Create new user chat document
        ai_response = await generate_chat_response([{"role": "user", "content": chat_message.message}], persona)
        user_chat = {
            "user_id": persona["user_id"],
            "threads": [{
                "thread_id": chat_message.thread_id,
                "persona_id": chat_message.persona_id,
                "messages": [
                    user_msg,
                    {
                        "sender": "ai",
                        "message": ai_response,
                        "timestamp": datetime.utcnow()
                    }
                ]
            }]
        }
        await db.chats.insert_one(user_chat)
    elif not thread_found:
        # Create new thread in existing user chat
        ai_response = await generate_chat_response([{"role": "user", "content": chat_message.message}], persona)
        new_thread = {
            "thread_id": chat_message.thread_id,
            "persona_id": chat_message.persona_id,
            "messages": [
                user_msg,
                {
                    "sender": "ai",
                    "message": ai_response,
                    "timestamp": datetime.utcnow()
                }
            ]
        }
        await db.chats.update_one(
            {"user_id": persona["user_id"]},
            {"$push": {"threads": new_thread}}
        )
    else:
        # Update the existing thread with new messages
        await db.chats.replace_one({"_id": user_chat["_id"]}, user_chat)

    await db.personas.update_one(
        {"_id": ObjectId(chat_message.persona_id)},
        {"$set": {"last_interaction": datetime.utcnow()}}
    )

    return ChatResponse(
        response=ai_response,
        thread_id=chat_message.thread_id,
        persona_id=chat_message.persona_id,
        timestamp=datetime.utcnow()
    )