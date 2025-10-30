from fastapi import APIRouter, HTTPException
from app.services.scheduler_service import (
    start_mood_checkin_scheduler, 
    test_mood_greeting, 
    get_mood_stats,
    list_mood_scheduler_jobs,
    check_personas_for_mood_greeting,
    check_user_mood_preference,
    update_user_mood_preference
)
from database.supabase_db import get_client
import requests
from bs4 import BeautifulSoup

router = APIRouter()

@router.post("/start-mood-scheduler")
async def initialize_mood_scheduler():
    """Start the mood check-in scheduler"""
    try:
        await start_mood_checkin_scheduler()
        return {"message": "Mood check-in scheduler started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting scheduler: {str(e)}")

@router.post("/test-mood-greeting/{persona_id}")
async def trigger_test_mood_greeting(persona_id: str):
    """Manually trigger a mood greeting for testing"""
    try:
        print(f"Triggering test mood greeting for persona_id: {persona_id}")  # Debug print
        result = await test_mood_greeting(persona_id)
        print(result)  # Debug print to verify the result
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/check-all-personas")
async def manual_persona_check():
    """Manually run the persona check for mood greetings"""
    try:
        await check_personas_for_mood_greeting()
        return {"message": "Persona mood check completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/mood-stats")
async def mood_message_statistics():
    """Get mood message statistics"""
    try:
        stats = await get_mood_stats()
        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats["error"])
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/mood-jobs")
async def get_mood_jobs():
    """Get list of mood-related scheduled jobs"""
    try:
        jobs = list_mood_scheduler_jobs()
        return {
            "total_mood_jobs": len(jobs),
            "jobs": jobs
        }
    except Exception as e:
        return {"error": str(e), "jobs": []}

@router.get("/persona-mood-messages/{persona_id}")
async def get_persona_mood_messages(persona_id: str):
    """Get all mood messages for a specific persona"""
    try:
        client = get_client()
        
        messages_result = client.table("mood_messages").select("*").eq(
            "persona_id", persona_id
        ).order("timestamp", desc=True).execute()
        
        return {
            "persona_id": persona_id,
            "count": len(messages_result.data),
            "messages": [
                {
                    "id": msg["id"],
                    "message": msg["message"],
                    "timestamp": msg["timestamp"],
                    "type": msg["type"],
                    "delivered": msg.get("delivered", False)
                }
                for msg in messages_result.data
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/undelivered-mood-messages/{user_id}")
async def get_undelivered_mood_messages(user_id: str):
    """Get undelivered mood messages for a user (for frontend polling)"""
    try:
        client = get_client()
        
        # Get undelivered mood messages for this user
        messages_result = client.table("mood_messages").select(
            "*, personas(name, thread_id)"
        ).eq("user_id", user_id).eq("delivered", False).order("timestamp", desc=False).execute()
        
        if not messages_result.data:
            return {"count": 0, "messages": []}
        
        # Mark messages as delivered
        message_ids = [msg["id"] for msg in messages_result.data]
        client.table("mood_messages").update({"delivered": True}).in_("id", message_ids).execute()
        
        return {
            "count": len(messages_result.data),
            "messages": [
                {
                    "id": msg["id"],
                    "persona_id": msg["persona_id"],
                    "persona_name": msg["personas"]["name"] if msg.get("personas") else "Unknown",
                    "thread_id": msg["personas"]["thread_id"] if msg.get("personas") else None,
                    "message": msg["message"],
                    "timestamp": msg["timestamp"],
                    "type": msg["type"]
                }
                for msg in messages_result.data
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mark-mood-delivered/{message_id}")
async def mark_mood_message_delivered(message_id: str):
    """Mark a specific mood message as delivered"""
    try:
        client = get_client()
        
        result = client.table("mood_messages").update({"delivered": True}).eq("id", message_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Mood message not found")
        
        return {"message": "Mood message marked as delivered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/personas-needing-checkin")
async def get_personas_needing_checkin():
    """Get list of personas that need mood check-ins"""
    try:
        from datetime import datetime, timedelta
        client = get_client()
        
        current_time = datetime.utcnow()
        twelve_hours_ago = current_time - timedelta(hours=12)
        
        # Get personas with last_interaction older than 12 hours
        personas_result = client.table("personas").select("*").or_(
            f"last_interaction.lt.{twelve_hours_ago.isoformat()},last_interaction.is.null"
        ).execute()
        
        return {
            "count": len(personas_result.data),
            "personas": [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "last_interaction": p.get("last_interaction"),
                    "user_id": p["user_id"]
                }
                for p in personas_result.data
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mood-preference/{user_id}")
async def get_user_mood_preference(user_id: str):
    """Get user's mood check-in preference"""
    try:
        enabled = await check_user_mood_preference(user_id)
        return {"user_id": user_id, "mood_checkin_enabled": enabled}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mood-preference/{user_id}")
async def set_user_mood_preference(user_id: str, enabled: bool):
    """Update user's mood check-in preference"""
    try:
        result = await update_user_mood_preference(user_id, enabled)
        
        if result["success"]:
            return {
                "message": f"Mood check-in preference {'enabled' if enabled else 'disabled'} for user {user_id}",
                "user_id": user_id,
                "mood_checkin_enabled": enabled
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/toggle-mood-preference/{user_id}")
async def toggle_user_mood_preference(user_id: str):
    """Toggle user's mood check-in preference"""
    try:
        # Get current preference
        current_enabled = await check_user_mood_preference(user_id)
        
        # Toggle it
        new_enabled = not current_enabled
        result = await update_user_mood_preference(user_id, new_enabled)
        
        if result["success"]:
            return {
                "message": f"Mood check-in preference {'enabled' if new_enabled else 'disabled'} for user {user_id}",
                "user_id": user_id,
                "mood_checkin_enabled": new_enabled,
                "previous_state": current_enabled
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
