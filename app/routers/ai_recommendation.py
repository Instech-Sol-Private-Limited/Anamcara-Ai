from fastapi import FastAPI, Request, APIRouter, HTTPException
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI
from database.supabase_db import get_client
import numpy as np
import json, os
from pydantic import BaseModel
from typing import Optional
import requests
import httpx
from datetime import datetime
import base64
from io import BytesIO

router = APIRouter()

from datetime import datetime

# ------------------------------------------------
# Setup
# ------------------------------------------------
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
openai_async_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

supabase = get_client()
# NEW: SDXL Server URL (GPU system ka IP aur port)
SDXL_SERVER_URL = os.getenv("SDXL_SERVER_URL", "http://192.168.18.61:8001")
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

# ================================================
# NEW: Image Generation Models and Endpoints
# ================================================

class ImageGenerationRequest(BaseModel):
    user_id: str
    prompt: str
    negative_prompt: Optional[str] = "blurry, bad quality, distorted"
    width: Optional[int] = 768
    height: Optional[int] = 768
    num_inference_steps: Optional[int] = 20
    guidance_scale: Optional[float] = 7.5

async def generate_image_with_openai(prompt: str, size: str = "1024x1024") -> Optional[str]:
    """
    Generate image using OpenAI DALL-E
    Returns base64 encoded image string or None if failed
    """
    try:
        response = await openai_async_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality="standard",
            n=1,
        )
        
        image_url = response.data[0].url
        
        # Download image and convert to base64
        img_response = requests.get(image_url)
        img_response.raise_for_status()
        
        # Convert to base64
        image_base64 = base64.b64encode(img_response.content).decode('utf-8')
        return image_base64
        
    except Exception as e:
        print(f"OpenAI DALL-E generation failed: {str(e)}")
        return None

async def generate_image_with_stable_diffusion(
    prompt: str, 
    negative_prompt: str,
    width: int,
    height: int,
    num_inference_steps: int,
    guidance_scale: float
) -> Optional[str]:
    """
    Generate image using Stable Diffusion (SDXL)
    Returns base64 encoded image string or None if failed
    """
    try:
        # Check if SDXL server is healthy
        try:
            health_check = requests.get(f"{SDXL_SERVER_URL}/health", timeout=5)
            if health_check.status_code != 200:
                return None
        except requests.exceptions.RequestException:
            return None

        # SDXL server ko request bhejein
        response = requests.post(
            f"{SDXL_SERVER_URL}/generate",
            json={
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "num_inference_steps": num_inference_steps,
                "guidance_scale": guidance_scale
            },
            timeout=120  # 2 minutes timeout
        )

        if response.status_code != 200:
            return None

        result = response.json()
        return result.get("image")  # Already base64 encoded
        
    except Exception as e:
        print(f"Stable Diffusion generation failed: {str(e)}")
        return None

@router.post("/api/generate-image")
async def generate_image(request: ImageGenerationRequest):
    """
    Generate image with fallback system:
    TIER 1: OpenAI DALL-E (Best quality)
    TIER 2: Stable Diffusion SDXL (Fallback)
    """
    generation_method = None
    image_base64 = None
    
    # ========================================================================
    # TIER 1: Try OpenAI DALL-E
    # ========================================================================
    try:
        print(f" TIER 1: Attempting OpenAI DALL-E generation...")
        # Convert width/height to DALL-E size format
        # DALL-E 3 supports: "1024x1024", "1792x1024", "1024x1792"
        if request.width >= request.height:
            if request.width >= 1792:
                size = "1792x1024"
            else:
                size = "1024x1024"
        else:
            size = "1024x1792"
        
        image_base64 = await generate_image_with_openai(request.prompt, size)
        
        if image_base64:
            generation_method = "openai_dalle3"
            print(f" TIER 1 SUCCESS: OpenAI DALL-E generated image")
            
    except Exception as e:
        print(f" TIER 1 FAILED: {str(e)}")
    
    # ========================================================================
    # TIER 2: Fallback to Stable Diffusion
    # ========================================================================
    if not image_base64:
        try:
            print(f" TIER 2: Falling back to Stable Diffusion generation...")
            image_base64 = await generate_image_with_stable_diffusion(
                prompt=request.prompt,
                negative_prompt=request.negative_prompt,
                width=request.width,
                height=request.height,
                num_inference_steps=request.num_inference_steps,
                guidance_scale=request.guidance_scale
            )
            
            if image_base64:
                generation_method = "stable_diffusion"
                print(f" TIER 2 SUCCESS: Stable Diffusion generated image")
                
        except Exception as e:
            print(f" TIER 2 FAILED: {str(e)}")
    
    # ========================================================================
    # Check if any method succeeded
    # ========================================================================
    if not image_base64:
        raise HTTPException(
            status_code=503,
            detail="All image generation services are currently unavailable. Please try again later."
        )
    
    # ========================================================================
    # Save to database and return
    # ========================================================================
    try:
        # User event track karein
        supabase.table("user_events").insert({
            "user_id": request.user_id,
            "event": "image_generated",
            "page": "image_generation",
            "metadata": {
                "prompt": request.prompt,
                "generation_method": generation_method
            },
            "timestamp": datetime.utcnow().isoformat()
        }).execute()

        # Generated image ko database mein save karein
        supabase.table("generated_images").insert({
            "user_id": request.user_id,
            "prompt": request.prompt,
            "image_base64": image_base64,
            "generation_method": generation_method,
            "timestamp": datetime.utcnow().isoformat()
        }).execute()

        return {
            "status": "success",
            "user_id": request.user_id,
            "image": image_base64,  # Base64 encoded image
            "prompt": request.prompt,
            "generation_method": generation_method,
            "message": f"Image generated successfully using {generation_method}!"
        }
        
    except Exception as e:
        # Even if database save fails, return the image
        return {
            "status": "success",
            "user_id": request.user_id,
            "image": image_base64,
            "prompt": request.prompt,
            "generation_method": generation_method,
            "message": f"Image generated successfully using {generation_method}! (Note: Database save failed)",
            "warning": str(e)
        }

@router.get("/api/user-images/{user_id}")
async def get_user_images(user_id: str, limit: int = 10):
    """
    User ki previously generated images retrieve karein
    """
    try:
        data = supabase.table("generated_images")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("timestamp", desc=True)\
            .limit(limit)\
            .execute()
        
        return {
            "status": "success",
            "user_id": user_id,
            "images": data.data or [],
            "count": len(data.data) if data.data else 0
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving images: {str(e)}"
        )

@router.get("/api/sdxl-health")
async def check_sdxl_health():
    """
    SDXL server ki health check karein
    """
    try:
        response = requests.get(f"{SDXL_SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            return {
                "status": "healthy",
                "sdxl_server": SDXL_SERVER_URL,
                "message": "SDXL server is running"
            }
        else:
            return {
                "status": "unhealthy",
                "sdxl_server": SDXL_SERVER_URL,
                "message": "SDXL server is not responding properly"
            }
    except requests.exceptions.RequestException as e:
        return {
            "status": "down",
            "sdxl_server": SDXL_SERVER_URL,
            "message": f"Cannot connect to SDXL server: {str(e)}"
        }

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