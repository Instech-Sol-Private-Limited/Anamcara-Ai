# # app/services/numerology_service.py

# import json
# with open("app/data/numerology_meanings.json") as f:
#     meanings = json.load(f)

# def reduce_number(n):
#     if n in [11, 22, 33]: return n
#     while n > 9: n = sum(int(d) for d in str(n))
#     return n

# def life_path(dob):
#     digits = [int(c) for c in dob if c.isdigit()]
#     return reduce_number(sum(digits))

# def expression(name):
#     values = {c: (ord(c) - 64) % 9 or 9 for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}
#     return reduce_number(sum(values.get(c, 0) for c in name.upper() if c.isalpha()))

# def soul_urge(name):
#     vowels = "AEIOU"
#     values = {c: (ord(c) - 64) % 9 or 9 for c in vowels}
#     return reduce_number(sum(values.get(c, 0) for c in name.upper() if c in vowels))

# def interpret(n): return meanings.get(str(n), "No meaning found.")


# app/services/numerology_service.py
import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load meanings from JSON
with open("app/data/numerology_meanings.json") as f:
    meanings = json.load(f)


# ---------- Core Numerology Calculations ----------
def reduce_number(n):
    if n in [11, 22, 33]:  # Master numbers
        return n
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


def life_path(dob):
    digits = [int(c) for c in dob if c.isdigit()]
    return reduce_number(sum(digits))


def expression(name):
    values = {c: (ord(c) - 64) % 9 or 9 for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}
    return reduce_number(sum(values.get(c, 0) for c in name.upper() if c.isalpha()))


def soul_urge(name):
    vowels = "AEIOU"
    values = {c: (ord(c) - 64) % 9 or 9 for c in vowels}
    return reduce_number(sum(values.get(c, 0) for c in name.upper() if c in vowels))


def interpret(n):
    return meanings.get(str(n), "No meaning found.")


# ---------- OpenAI Enhancement ----------
def enhance_with_openai(name, dob, number_type, number, base_meaning):
    """
    Enhance numerology reading with OpenAI for a given number type.
    """
    prompt = f"""
    You are a master numerologist. The user’s name is {name} and their birth date is {dob}.
    Their {number_type} Number is {number}.

    Base meaning: {base_meaning}

    Please provide a warm, friendly, and easy-to-understand {number_type} reading with points that includes:
    1. Personality traits (positive & negative)
    2. Potential strengths
    3. Challenges they might face
    4. Career and relationship guidance
    5. Life themes
    6. Use their name a few times for personalization.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a warm, insightful numerologist providing personalized readings."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8
    )

    return response.choices[0].message.content
