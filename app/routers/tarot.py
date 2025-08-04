from fastapi import APIRouter
from pydantic import BaseModel
from app.services.tarot_service import generate_spread_with_interpretation

router = APIRouter(prefix="/tarot", tags=["Tarot"])

class TarotRequest(BaseModel):
    name: str
    spread: str  # 'single', 'three', or 'relationship'
    dream: str = None

@router.post("/reading")
def tarot_reading(payload: TarotRequest):
    return generate_spread_with_interpretation(payload.name, payload.spread, payload.dream)
