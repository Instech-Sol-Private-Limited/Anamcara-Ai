# # app/services/horoscope_service.py

# import os
# import requests
# from datetime import datetime
# from dotenv import load_dotenv
# from requests.auth import HTTPBasicAuth

# load_dotenv()

# USER_ID = os.getenv("ASTROLOGY_API_USER_ID")
# API_KEY = os.getenv("ASTROLOGY_API_KEY")

# def get_zodiac(birthdate: str) -> str:
#     dob = datetime.strptime(birthdate, "%Y-%m-%d")
#     month, day = dob.month, dob.day
#     signs = [
#         ("Capricorn", 1, 19), ("Aquarius", 2, 18), ("Pisces", 3, 20),
#         ("Aries", 4, 19), ("Taurus", 5, 20), ("Gemini", 6, 20),
#         ("Cancer", 7, 22), ("Leo", 8, 22), ("Virgo", 9, 22),
#         ("Libra", 10, 22), ("Scorpio", 11, 21), ("Sagittarius", 12, 21),
#         ("Capricorn", 12, 31)
#     ]
#     for sign, m, d in signs:
#         if month == m and day <= d:
#             return sign.lower()
#     return "capricorn"

# def fetch_horoscope(sign: str) -> dict:
#     url = f"https://json.astrologyapi.com/v1/sun_sign_prediction/daily/{sign.lower()}"
#     response = requests.get(url, auth=HTTPBasicAuth(USER_ID, API_KEY), timeout=5)

#     if response.status_code == 200:
#         return response.json()
#     else:
#         raise Exception(f"AstrologyAPI Error: {response.status_code} - {response.text}")


import os, requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_NINJAS_KEY")  # Key from API Ninjas

def get_zodiac(birthdate: str) -> str:
    dob = datetime.strptime(birthdate, "%Y-%m-%d")
    month, day = dob.month, dob.day
    
    # Check each zodiac sign with proper date range logic
    if (month == 3 and day >= 21) or (month == 4 and day <= 19):
        return "aries"
    elif (month == 4 and day >= 20) or (month == 5 and day <= 20):
        return "taurus"
    elif (month == 5 and day >= 21) or (month == 6 and day <= 21):
        return "gemini"
    elif (month == 6 and day >= 22) or (month == 7 and day <= 22):
        return "cancer"
    elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
        return "leo"
    elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
        return "virgo"
    elif (month == 9 and day >= 23) or (month == 10 and day <= 23):
        return "libra"
    elif (month == 10 and day >= 24) or (month == 11 and day <= 21):
        return "scorpio"
    elif (month == 11 and day >= 22) or (month == 12 and day <= 21):
        return "sagittarius"
    elif (month == 12 and day >= 22) or (month == 1 and day <= 19):
        return "capricorn"
    elif (month == 1 and day >= 20) or (month == 2 and day <= 18):
        return "aquarius"
    elif (month == 2 and day >= 19) or (month == 3 and day <= 20):
        return "pisces"
    else:
        return "capricorn"  # fallback

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