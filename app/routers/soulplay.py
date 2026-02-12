from fastapi import APIRouter
from models.schemas import SoulPlayRequest, SoulPlayResponse
from app.services.ai_soulplay_recommender import rank_media

router = APIRouter()

@router.post("/recommend_soulplay", response_model=SoulPlayResponse)
async def recommend_soulplay(payload: SoulPlayRequest):

    ranked_items = rank_media(
        mood=payload.mood,
        tags=payload.tags,
        items=[i.dict() for i in payload.items]
    )

    return {
        "mood": payload.mood,
        "platform": payload.items[0].platform,
        "recommendations": ranked_items
    }

