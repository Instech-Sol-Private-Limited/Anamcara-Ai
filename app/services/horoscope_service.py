# app/services/horoscope_service.py

import os, requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_NINJAS_KEY")  # Key from API Ninjas

def get_zodiac(birthdate: str) -> str:
    dob = datetime.strptime(birthdate, "%Y-%m-%d")
    month, day = dob.month, dob.day
    signs = [
        ("Capricorn", 1, 19), ("Aquarius", 2, 18), ("Pisces", 3, 20),
        ("Aries", 4, 19), ("Taurus", 5, 20), ("Gemini", 6, 20),
        ("Cancer", 7, 22), ("Leo", 8, 22), ("Virgo", 9, 22),
        ("Libra", 10, 22), ("Scorpio", 11, 21), ("Sagittarius", 12, 21),
        ("Capricorn", 12, 31)
    ]
    for sign, m, d in signs:
        if month == m and day <= d:
            return sign.lower()
    return "capricorn"

def fetch_horoscope(sign: str) -> dict:
    url = "https://api.api-ninjas.com/v1/horoscope"
    headers = {
        "X-Api-Key": API_KEY
    }
    params = {"zodiac": sign}
    response = requests.get(url, headers=headers, params=params, timeout=5)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Horoscope API Error: {response.status_code}: {response.text}")
