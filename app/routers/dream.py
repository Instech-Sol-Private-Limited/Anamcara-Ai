# app/routers/dream.py

from fastapi import APIRouter, Body
from app.services.dream_service import extract_keywords, match_keywords_to_tarot, interpret_with_gpt
from typing import List, Optional

router = APIRouter(prefix="/dream", tags=["Dream"])

@router.post("/interpret")
def interpret_dream(
    dream: str = Body(...),
    cards: Optional[List[dict]] = Body(default=None)
):
    # Extract dream keywords
    keywords = extract_keywords(dream)

    # If cards provided → try tarot matching
    matches = []
    if cards:
        matches = match_keywords_to_tarot(keywords, cards)

    # Always get GPT-powered dream interpretation
    gpt_interpretation = interpret_with_gpt(dream, keywords, matches)

    return {
        "keywords": keywords,
        "matches": matches,
        "AI_interpretation": gpt_interpretation
    }