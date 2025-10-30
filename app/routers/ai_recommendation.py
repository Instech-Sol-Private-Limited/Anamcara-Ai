from fastapi import FastAPI, Request, APIRouter, HTTPException
from dotenv import load_dotenv
from openai import OpenAI
from database.supabase_db import get_client
import numpy as np
import json, os
from pydantic import BaseModel
from typing import Optional
router = APIRouter()

from datetime import datetime

# ------------------------------------------------
# Setup
# ------------------------------------------------
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

supabase = get_client()

# ------------------------------------------------
# Load Ecosystem Knowledge Base
# ------------------------------------------------
with open("anamcara_modules.json", "r", encoding="utf-8") as f:
    kb = json.load(f)

def extract_modules(data):
    modules = {}
    for cat in data["AnamcaraAI"]["ecosystem"].values():
        for name, info in cat.items():
            modules[name] = info
    return modules

modules = extract_modules(kb)

# ------------------------------------------------
# Embedding Helpers
# ------------------------------------------------
def get_embedding(text: str):
    """Get embedding with error handling for quota issues"""
    try:
        res = client.embeddings.create(input=text, model="text-embedding-3-small")
        return np.array(res.data[0].embedding)
    except Exception as e:
        # Handle quota/rate limit errors
        if hasattr(e, 'status_code') and e.status_code == 429:
            raise HTTPException(
                status_code=503,
                detail="OpenAI API credits expired. Please contact administration to resolve this issue."
            )
        # Re-raise other errors
        raise

def cosine(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Initialize embeddings cache as None - will be computed on first request
module_embeddings = None

def initialize_embeddings():
    """Initialize embeddings on first request instead of module load"""
    global module_embeddings
    if module_embeddings is None:
        try:
            module_embeddings = {m: get_embedding(v["purpose"]) for m, v in modules.items()}
        except HTTPException:
            # If quota exceeded during initialization, raise it
            raise
        except Exception as e:
            print(f"Error initializing embeddings: {e}")
            raise HTTPException(
                status_code=503,
                detail="Failed to initialize AI recommendations. Please contact administration."
            )
    return module_embeddings

# ------------------------------------------------
# Supabase Helpers
# ------------------------------------------------
def save_event(user_id: str, event: str, page: str):
    supabase.table("user_events").insert({
        "user_id": user_id,
        "event": event,
        "page": page,
        "timestamp": datetime.utcnow().isoformat()
    }).execute()

def get_user_events(user_id: str):
    data = supabase.table("user_events").select("*").eq("user_id", user_id).order("timestamp", desc=True).limit(5).execute()
    return data.data or []

def get_user_memory(user_id: str):
    res = supabase.table("user_memory").select("*").eq("user_id", user_id).execute()
    if res.data:
        return res.data[0].get("recommended", [])
    return []

def update_user_memory(user_id: str, new_modules):
    seen = set(get_user_memory(user_id))
    seen.update(new_modules)
    data = {"user_id": user_id, "recommended": list(seen)}
    supabase.table("user_memory").upsert(data).execute()

class TrackEvent(BaseModel):
    user_id: str
    event: str
    page: Optional[str] = None
    metadata: Optional[dict] = None

# ------------------------------------------------
# API Endpoints
# ------------------------------------------------
@router.post("/api/track")
async def track_event(data: TrackEvent):
    """Track user events like scrolls, plays, posts"""
    user_id = data.user_id
    event_data = data.dict()
    event_data["timestamp"] = datetime.utcnow().isoformat()

    supabase.table("user_events").insert(event_data).execute()

    return {
        "status": "ok",
        "message": "Event tracked successfully",
        "event": event_data
    }

# ------------------------------------------------
# Recommend with Supabase Memory
# ------------------------------------------------
@router.get("/api/recommend/{user_id}")
def recommend(user_id: str):
    try:
        # Initialize embeddings if not already done
        embeddings = initialize_embeddings()
        
        activities = get_user_events(user_id)
        if not activities:
            return {"message": "No recent activity found", "recommendation": None}

        activity_text = " ".join([f"{a['event']} on {a.get('page', '')}" for a in activities])
        
        # Get user embedding with error handling
        try:
            user_emb = get_embedding(activity_text)
        except HTTPException:
            raise
        except Exception as e:
            return {
                "status": "error",
                "message": "OpenAI API credits expired. Please contact administration to resolve this issue.",
                "error": str(e)
            }

        seen = set(get_user_memory(user_id))
        scores = {
            m: cosine(user_emb, emb)
            for m, emb in embeddings.items()
            if m not in seen
        }

        if not scores:
            return {"message": "All modules already recommended", "recommendation": None}

        top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        top_modules = [
            {
                "module": name,
                "url": modules[name].get("url", "N/A"),
                "purpose": modules[name]["purpose"],
                "score": float(score)
            }
            for name, score in top
        ]

        prompt = f"""
        The user recently performed: {activity_text}.
        Based on semantic similarity, the top 3 modules are:
        {json.dumps(top_modules, indent=2)}

        You are an AI guide in the Anamcara ecosystem.
        Recommend the single best module for this user's interest
        and write a short, warm, response of (2 sentences) that we have these modules available and you like to try it something like response you write.
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a friendly, soulful AI assistant inside Anamcara."},
                    {"role": "user", "content": prompt}
                ]
            )
            reply = response.choices[0].message.content.strip()
        except Exception as e:
            if hasattr(e, 'status_code') and e.status_code == 429:
                return {
                    "status": "error",
                    "message": "OpenAI API credits expired. Please contact administration to resolve this issue.",
                    "recommendations": top_modules
                }
            reply = "We have found some great recommendations for you based on your activity!"

        update_user_memory(user_id, [m["module"] for m in top_modules])

        return {
            "user_id": user_id,
            "recent_activity": activity_text,
            "recommendations": top_modules,
            "agent_response": reply
        }
    
    except HTTPException:
        # Re-raise HTTPException to be handled by FastAPI
        raise
    except Exception as e:
        return {
            "status": "error",
            "message": "OpenAI API credits expired. Please contact administration to resolve this issue.",
            "error": str(e)
        }