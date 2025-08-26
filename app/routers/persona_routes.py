from fastapi import APIRouter, HTTPException
from models.schemas import PersonaCreate, PersonaResponse
from models.mongo_helpers import serialize_doc
from database.mongodb import db
# from services.scheduler_service import schedule_daily_greeting
from datetime import datetime
import uuid

router = APIRouter()

@router.post("/", response_model=PersonaResponse)
async def create_persona(persona: PersonaCreate):
    from database.mongodb import db
    print("DB in route:", db)
    thread_id = str(uuid.uuid4())
    doc = {
        "name": persona.name,
        "gender": persona.gender,
        "personality_traits": persona.personality_traits,
        "user_id": persona.user_id,
        "thread_id": thread_id,
        "created_at": datetime.utcnow(),
        "last_interaction": datetime.utcnow()
    }
    result = await db.personas.insert_one(doc)
    # await schedule_daily_greeting(str(result.inserted_id))
    saved = await db.personas.find_one({"_id": result.inserted_id})
    return serialize_doc(saved)

@router.get("/{user_id}")
async def get_user_personas(user_id: str):
    from database.mongodb import db
    print("DB in get_user_personas:", db)
    result = await db.personas.find({"user_id": user_id}).to_list(length=100)
    return [serialize_doc(p) for p in result]
