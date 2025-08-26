import random
import json
from app.services.gpt_handler import generate_poetic_summary

with open("app/data/tarot_cards(1).json", "r", encoding="utf-8") as f:
    cards_data = json.load(f)

# Mapping dream keywords to cards
dream_keyword_mapping = {
    "water": ["The Moon", "Temperance"],
    "flying": ["The Fool", "The Star"],
    "darkness": ["The Devil", "Death"],
}

# Updated spread positions to match frontend
spread_positions = {
    "single": ["Guidance"],
    "three": ["Past", "Present", "Future"],
    "situation": ["Situation", "Action", "Outcome"],
    "relationship": ["Your Energy", "Their Energy", "Connection"],
    "celtic": [
        "Present", "Challenge", "Past", "Future", "Crown",
        "Foundation", "Your Approach", "External Influences",
        "Hopes & Fears", "Outcome"
    ]
}

# Temporary in-memory storage (use DB in production)
readings_storage = {}

def generate_spread(name, spread_type):
    positions = spread_positions.get(spread_type, ["Guidance"])
    drawn_cards = random.sample(cards_data, len(positions))

    cards_output = []
    interpretations = []

    for i, pos in enumerate(positions):
        card = drawn_cards[i]
        orientation = random.choice(["upright", "reversed"])
        meaning = card[orientation]
        cards_output.append({
            "name": card["name"],
            "position": pos,
            "orientation": orientation,
            "meaning": meaning
        })
        interpretations.append(f"{name}, in the '{pos}' position, you drew '{card['name']}' ({orientation.title()}): {meaning}")

    return {
        "cards": cards_output,
        "interpretations": interpretations
    }

def generate_summary(name, cards_output, dream=None):
    keywords_matched = []
    if dream:
        for card in cards_output:
            for keyword, related_cards in dream_keyword_mapping.items():
                if keyword in dream.lower() and card["name"] in related_cards:
                    keywords_matched.append((keyword, card["name"], card["meaning"]))

    dream_link = None
    if keywords_matched:
        keyword, card_name, shared_meaning = keywords_matched[0]
        dream_link = f"The image of '{keyword}' in your dream, {name}, might echo the themes of '{card_name}' — such as: {shared_meaning}"

    summary = generate_poetic_summary(name=name, cards=cards_output, dream_link=dream_link)
    return {
        "cards": cards_output,
        "dream_link": dream_link,
        "summary": summary
    }
