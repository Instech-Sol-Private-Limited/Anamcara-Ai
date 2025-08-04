import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def generate_poetic_summary(name, cards, dream_link=None):
    card_descriptions = "\n".join([f"- {card['name']} ({card['orientation']})" for card in cards])
    prompt = f"""
You are a poetic spiritual guide. Write a 3-4 line poetic summary for {name}, based on their Tarot reading.
The drawn cards are:
{card_descriptions}

Dream link (if any): {dream_link or "None"}

Respond in a poetic tone, combining mystical symbolism and emotional depth. Make it inspiring.
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9
    )

    return response.choices[0].message.content.strip()
