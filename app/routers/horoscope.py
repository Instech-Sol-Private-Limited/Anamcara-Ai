# app/routers/horoscope.py

from fastapi import APIRouter
from app.services.horoscope_service import get_zodiac, fetch_horoscope

router = APIRouter(prefix="/horoscope", tags=["Horoscope"])

@router.get("/")
def daily_horoscope(dob: str):
    sign = get_zodiac(dob)
    data = fetch_horoscope(sign)
    return {"sign": sign.capitalize(), "date": data.get("date"), "horoscope": data.get("horoscope")}
