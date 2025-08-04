from fastapi import APIRouter
from pydantic import BaseModel
from app.services.gpt_handler import generate_poetic_summary

router = APIRouter()

class SummaryRequest(BaseModel):
    dream: str
    tarot_summary: list[str]
    horoscope: str

@router.post("/summary/")
def poetic_summary(request: SummaryRequest):
    summary = generate_poetic_summary(
        dream=request.dream,
        tarot_summary=request.tarot_summary,
        horoscope=request.horoscope
    )
    return {"summary": summary}
