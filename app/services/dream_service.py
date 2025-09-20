import spacy
import json
from typing import List
from openai import OpenAI
import os
from dotenv import load_dotenv  


load_dotenv()  # take environment variables from .env.

client = OpenAI()

# Load NLP model
nlp = spacy.load("en_core_web_md")

# Load dream symbol meanings
with open("app/data/dream_symbols.json", "r", encoding="utf-8") as f:
    dream_map = json.load(f)

# Load tarot card data
with open("app/data/tarot_cards(1).json", "r", encoding="utf-8") as f:
    tarot_data = json.load(f)

def extract_keywords(text: str) -> List[str]:
    doc = nlp(text)
    return [token.lemma_ for token in doc if token.pos_ in ['NOUN', 'PROPN']]

def match_keywords_to_tarot(keywords: List[str], cards: List[dict]) -> List[str]:
    matches = []
    for word in keywords:
        if word not in dream_map:
            continue
        dream_doc = nlp(dream_map[word])

        for card in cards:
            tarot_card = next((c for c in tarot_data if c["name"] == card["name"]), None)
            if not tarot_card:
                continue

            meanings = [tarot_card["upright"], tarot_card["reversed"]]
            for meaning in meanings:
                tarot_doc = nlp(meaning)
                similarity = dream_doc.similarity(tarot_doc)

                if similarity > 0.7:
                    matches.append(
                        f"The dream symbol '{word}' relates to '{card['name']}' ({card['orientation']}) – similarity: {similarity:.2f}"
                    )
                    break
    return matches

def interpret_with_gpt(dream: str, keywords: List[str], matches: List[str]) -> str:
    """Use GPT to generate a cohesive dream interpretation."""
    symbols_meanings = {k: dream_map.get(k, "") for k in keywords}
    prompt = f"""
    Dream: {dream}

    Extracted Keywords: {keywords}
    Symbol Meanings: {symbols_meanings}
    Tarot Matches: {matches if matches else 'None'}

    Please provide a structured, poetic, and insightful interpretation of this dream. 
    Connect the dream symbols to emotions, psychology, and possible real-life reflections.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # switch to "gpt-4o" if you want full GPT-4
        messages=[
            {"role": "system", "content": "You are a mystical dream interpreter who combines psychology and symbolism."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()
