# routes/persona_routes.py
from fastapi import APIRouter, HTTPException
from models.schemas import PersonaCreate, PersonaResponse
from models.supabase_helpers import serialize_doc, serialize_docs, convert_personality_traits_to_array
from database.supabase_db import get_client
# from services.scheduler_service import schedule_daily_greeting
from datetime import datetime
import uuid

router = APIRouter()

@router.post("/", response_model=PersonaResponse)
async def create_persona(persona: PersonaCreate):
    try:
        client = get_client()
        thread_id = str(uuid.uuid4())
        
        persona_data = {
            "name": persona.name,
            "gender": persona.gender,
            "personality_traits": convert_personality_traits_to_array(persona.personality_traits),
            "user_id": persona.user_id,
            "thread_id": thread_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_interaction": datetime.utcnow().isoformat()
        }
        
        # Insert persona into Supabase
        result = client.table("personas").insert(persona_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create persona")
        
        created_persona = result.data[0]
        persona_id = created_persona["id"]
        
        # Schedule daily greeting
        # await schedule_daily_greeting(str(persona_id))
        
        return serialize_doc(created_persona)
        
    except Exception as e:
        print(f"Error creating persona: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create persona: {str(e)}")

@router.get("/{user_id}")
async def get_user_personas(user_id: str):
    try:
        client = get_client()
        
        # Get all personas for the user
        result = client.table("personas").select("*").eq("user_id", user_id).execute()
        
        if not result.data:
            return []
        
        return serialize_docs(result.data)
        
    except Exception as e:
        print(f"Error getting user personas: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get personas: {str(e)}")

@router.get("/details/{persona_id}")
async def get_persona_by_id(persona_id: str):
    try:
        client = get_client()
        
        # Get specific persona
        result = client.table("personas").select("*").eq("id", persona_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Persona not found")
        
        return serialize_doc(result.data[0])
        
    except Exception as e:
        print(f"Error getting persona by ID: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get persona: {str(e)}")

@router.delete("/{persona_id}")
async def delete_persona(persona_id: str):
    try:
        client = get_client()
        
        # Delete persona (this will cascade delete related messages due to foreign key)
        result = client.table("personas").delete().eq("id", persona_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Persona not found")
        
        return {"message": "Persona deleted successfully"}
        
    except Exception as e:
        print(f"Error deleting persona: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete persona: {str(e)}")