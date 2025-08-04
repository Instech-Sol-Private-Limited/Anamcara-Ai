import spacy
import json
from typing import List

nlp = spacy.load("en_core_web_md")
def extract_keywords(text):
    doc = nlp(text)
    return [token.lemma_ for token in doc if token.pos_ in ['NOUN', 'PROPN']]
# Load dream symbol meanings
    
with open("app\data\dream_symbols.json", "r", encoding="utf-8") as f:
    dream_map = json.load(f)
# Load tarot card data (with upright and reversed meanings)
with open("app/data/tarot_cards(1).json", "r", encoding="utf-8") as f:
    tarot_data = json.load(f)
    print("Tarot data loaded successfully.",tarot_data)

def match_keywords_to_tarot(keywords: List[str], cards: List[dict]) -> List[str]:
    matches = []

    for word in keywords:
        print("this is the keyword@@@", word)
        if word not in dream_map:
            continue
        dream_doc = nlp(dream_map[word])

        for card in cards:
            tarot_card = next((c for c in tarot_data if c["name"] == card["name"]), None)
            print("All card names:@", [c["name"] for c in tarot_data])
            print("Current card to match:", card["name"])
            print("this is the tarot card@@@", tarot_card)
            if not tarot_card:
                continue

            meanings = [
                tarot_card["upright"],
                tarot_card["reversed"]
            ]

            for meaning in meanings:
                tarot_doc = nlp(meaning)
                similarity = dream_doc.similarity(tarot_doc)
                

                if similarity > 0.7: 
                    matches.append(
                        f"The dream symbol '{word}' relates to '{card['name']}' ({card['orientation']}) – similarity score: {similarity:.2f}"
                    )
                    break  # One match per card is enough

    return matches


