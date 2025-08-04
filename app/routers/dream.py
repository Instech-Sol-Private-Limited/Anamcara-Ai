# app/routers/dream.py

from fastapi import APIRouter, Body
from app.services.dream_service import extract_keywords, match_keywords_to_tarot

router = APIRouter(prefix="/dream", tags=["Dream"])

@router.post("/interpret")
def interpret_dream(dream: str = Body(...), cards: list = Body(...)):
    keywords = extract_keywords(dream)
    matches = match_keywords_to_tarot(keywords, cards)
    return {
        "keywords": keywords,
        "matches": matches
    }
