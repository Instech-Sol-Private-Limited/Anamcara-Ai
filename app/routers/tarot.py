from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.tarot_service import generate_spread, generate_summary, readings_storage
import uuid

router = APIRouter(prefix="/tarot", tags=["Tarot"])

class TarotRequest(BaseModel):
    name: str
    spread: str  # 'single', 'three', 'situation', 'relationship', 'celtic'

class TarotSummaryRequest(BaseModel):
    reading_id: str
    dream: str = None

@router.post("/reading")
def tarot_reading(payload: TarotRequest):
    # Generate spread
    result = generate_spread(payload.name, payload.spread)

    # Create a unique reading ID
    reading_id = str(uuid.uuid4())
    readings_storage[reading_id] = result["cards"]

    return {
        "reading_id": reading_id,
        "cards": result["cards"],
        "interpretations": result["interpretations"]
    }

@router.post("/summary")
def tarot_summary(payload: TarotSummaryRequest):
    # Retrieve the stored cards
    cards_output = readings_storage.get(payload.reading_id)
    if not cards_output:
        raise HTTPException(status_code=404, detail="Reading not found or expired.")

    # Generate summary with dream (if provided)
    summary_data = generate_summary("Your Reading", cards_output, payload.dream)
    return summary_data



