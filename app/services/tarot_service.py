
import random
import json
from app.services.gpt_handler import generate_poetic_summary

with open("app/data/tarot_cards(1).json", "r", encoding="utf-8") as f:
    cards_data = json.load(f)


dream_keyword_mapping = {
    "water": ["The Moon", "Temperance"],
    "flying": ["The Fool", "The Star"],
    "darkness": ["The Devil", "Death"],
}

spread_positions = {
    "single": ["Insight"],
    "three": ["Past", "Present", "Future"],
    "relationship": ["You", "Partner", "Challenge"]
}

def generate_spread_with_interpretation(name, spread_type, dream=None):
    positions = spread_positions.get(spread_type, ["Insight"])
    drawn_cards = random.sample(cards_data, len(positions))

    cards_output = []
    interpretations = []
    keywords_matched = []

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
        interpretations.append(f"{name}, for '{pos}', you drew '{card['name']}' ({orientation.title()}): {meaning}")

        if dream:
            for keyword, related_cards in dream_keyword_mapping.items():
                if keyword in dream.lower() and card["name"] in related_cards:
                    keywords_matched.append((keyword, card["name"], meaning))

    dream_link = None
    if keywords_matched:
        keyword, card_name, shared_meaning = keywords_matched[0]
        dream_link = f"The image of '{keyword}' in your dream, {name}, might echo the themes of '{card_name}' — such as: {shared_meaning}"

    summary = generate_poetic_summary(name=name, cards=cards_output, dream_link=dream_link)
    return {
        "cards": cards_output,
        "interpretations": interpretations,
        "dream_link": dream_link,
        "summary": summary
    }
