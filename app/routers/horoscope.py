# # app/routers/horoscope.py

# from fastapi import APIRouter
# from app.services.horoscope_service import get_zodiac, fetch_horoscope
# from datetime import datetime

# router = APIRouter(prefix="/horoscope", tags=["Horoscope"])

# @router.get("/")
# def daily_horoscope(dob: str, name: str = "Friend"):
#     sign = get_zodiac(dob)
#     data = fetch_horoscope(sign)
#     today = datetime.now().strftime("%A, %B %d, %Y")
    
#     return {
#         "message": f"Good morning, {name}! Here is your horoscope for today, {today}, based on your zodiac sign {sign.capitalize()}:",
#         "zodiac_sign": sign.capitalize(),
#         "prediction": data.get("prediction"),
#         "health": data.get("health"),
#         "love": data.get("love"),
#         "profession": data.get("profession"),
#         "lucky_number": f"Your lucky number today, {name}, might be {data.get('lucky_number')}.",
#         "lucky_color": f"The color that may bring you positive vibes today, {name}, is {data.get('lucky_color')}.",
#         "mood": data.get("mood"),
#     }


# app/routers/horoscope.py

from fastapi import APIRouter
from app.services.horoscope_service import get_zodiac, fetch_horoscope

router = APIRouter(prefix="/horoscope", tags=["Horoscope"])

@router.get("/")
def daily_horoscope(dob: str):
    sign = get_zodiac(dob)
    data = fetch_horoscope(sign)
    return {"sign": sign.capitalize(), "date": data.get("date"), "horoscope": data.get("horoscope")}