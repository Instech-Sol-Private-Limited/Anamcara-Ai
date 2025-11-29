from app.services.llm_gateway import llm_gateway
import asyncio
import random
from typing import List, Dict, Tuple

# Storage for readings (PRESERVED)
readings_storage = {}

# Complete Tarot Deck (PRESERVED - 78 Cards)
TAROT_DECK = {
    # Major Arcana (22 cards)
    "The Fool": "New beginnings, innocence, spontaneity, free spirit",
    "The Magician": "Manifestation, resourcefulness, power, inspired action",
    "The High Priestess": "Intuition, sacred knowledge, divine feminine, subconscious mind",
    "The Empress": "Femininity, beauty, nature, nurturing, abundance",
    "The Emperor": "Authority, establishment, structure, father figure",
    "The Hierophant": "Spiritual wisdom, religious beliefs, conformity, tradition",
    "The Lovers": "Love, harmony, relationships, values alignment, choices",
    "The Chariot": "Control, willpower, success, action, determination",
    "Strength": "Strength, courage, persuasion, influence, compassion",
    "The Hermit": "Soul searching, introspection, being alone, inner guidance",
    "Wheel of Fortune": "Good luck, karma, life cycles, destiny, turning point",
    "Justice": "Justice, fairness, truth, cause and effect, law",
    "The Hanged Man": "Pause, surrender, letting go, new perspectives",
    "Death": "Endings, change, transformation, transition, new beginnings",
    "Temperance": "Balance, moderation, patience, purpose, meaning",
    "The Devil": "Shadow self, attachment, addiction, restriction, sexuality",
    "The Tower": "Sudden change, upheaval, chaos, revelation, awakening",
    "The Star": "Hope, faith, purpose, renewal, spirituality, healing",
    "The Moon": "Illusion, fear, anxiety, subconscious, intuition",
    "The Sun": "Positivity, fun, warmth, success, vitality, joy",
    "Judgement": "Judgement, rebirth, inner calling, absolution, reckoning",
    "The World": "Completion, accomplishment, travel, fulfillment, success",
    
    # Minor Arcana - Wands (14 cards)
    "Ace of Wands": "Inspiration, creative spark, new initiative, potential",
    "Two of Wands": "Planning, making decisions, leaving comfort zone",
    "Three of Wands": "Progress, expansion, foresight, overseas opportunities",
    "Four of Wands": "Celebration, joy, harmony, relaxation, homecoming",
    "Five of Wands": "Conflict, disagreements, competition, tension",
    "Six of Wands": "Success, public recognition, progress, self-confidence",
    "Seven of Wands": "Challenge, competition, perseverance, defending position",
    "Eight of Wands": "Movement, fast paced change, action, alignment",
    "Nine of Wands": "Resilience, courage, persistence, test of faith",
    "Ten of Wands": "Burden, extra responsibility, hard work, completion",
    "Page of Wands": "Exploration, excitement, freedom, new ideas",
    "Knight of Wands": "Energy, passion, inspired action, adventure",
    "Queen of Wands": "Courage, confidence, independence, determination",
    "King of Wands": "Natural leader, vision, entrepreneur, honor",
    
    # Minor Arcana - Cups (14 cards)
    "Ace of Cups": "Love, new relationships, compassion, creativity",
    "Two of Cups": "Unified love, partnership, mutual attraction, connection",
    "Three of Cups": "Celebration, friendship, creativity, collaboration",
    "Four of Cups": "Meditation, contemplation, apathy, reevaluation",
    "Five of Cups": "Regret, failure, disappointment, pessimism, loss",
    "Six of Cups": "Revisiting the past, childhood memories, innocence, joy",
    "Seven of Cups": "Opportunities, choices, wishful thinking, illusion",
    "Eight of Cups": "Disappointment, abandonment, withdrawal, escapism",
    "Nine of Cups": "Contentment, satisfaction, gratitude, wish come true",
    "Ten of Cups": "Divine love, blissful relationships, harmony, alignment",
    "Page of Cups": "Creative opportunities, intuitive messages, curiosity",
    "Knight of Cups": "Creativity, romance, charm, imagination, beauty",
    "Queen of Cups": "Compassionate, caring, emotionally stable, intuitive",
    "King of Cups": "Emotionally balanced, diplomatic, compassion, devoted",
    
    # Minor Arcana - Swords (14 cards)
    "Ace of Swords": "Breakthrough, clarity, sharp mind, new ideas, truth",
    "Two of Swords": "Difficult decisions, weighing options, stalemate",
    "Three of Swords": "Heartbreak, emotional pain, sorrow, grief, hurt",
    "Four of Swords": "Rest, relaxation, meditation, contemplation, recuperation",
    "Five of Swords": "Conflict, defeat, winning at all costs, tension",
    "Six of Swords": "Transition, change, rite of passage, moving forward",
    "Seven of Swords": "Betrayal, deception, getting away with something, stealth",
    "Eight of Swords": "Negative thoughts, self-imposed restriction, imprisonment",
    "Nine of Swords": "Anxiety, worry, fear, depression, nightmares",
    "Ten of Swords": "Painful endings, deep wounds, betrayal, rock bottom",
    "Page of Swords": "New ideas, curiosity, thirst for knowledge, restless",
    "Knight of Swords": "Ambitious, action-oriented, driven to succeed, fast thinking",
    "Queen of Swords": "Independent, unbiased judgement, clear boundaries, direct",
    "King of Swords": "Mental clarity, intellectual power, authority, truth",
    
    # Minor Arcana - Pentacles (14 cards)
    "Ace of Pentacles": "New financial opportunity, prosperity, new venture, abundance",
    "Two of Pentacles": "Multiple priorities, time management, prioritization, adaptability",
    "Three of Pentacles": "Teamwork, collaboration, learning, implementation",
    "Four of Pentacles": "Saving money, security, conservatism, scarcity, control",
    "Five of Pentacles": "Financial loss, poverty, lack mindset, isolation, worry",
    "Six of Pentacles": "Giving, receiving, sharing wealth, generosity, charity",
    "Seven of Pentacles": "Long-term view, sustainable results, perseverance, investment",
    "Eight of Pentacles": "Apprenticeship, repetitive tasks, mastery, skill development",
    "Nine of Pentacles": "Abundance, luxury, self-sufficiency, financial independence",
    "Ten of Pentacles": "Wealth, financial security, family, long-term success, legacy",
    "Page of Pentacles": "Manifestation, financial opportunity, new job, skill development",
    "Knight of Pentacles": "Hard work, productivity, routine, conservatism, dedication",
    "Queen of Pentacles": "Nurturing, practical, providing financially, down-to-earth",
    "King of Pentacles": "Wealth, business, leadership, security, discipline, abundance"
}

# Spread types and their meanings (PRESERVED)
SPREAD_TYPES = {
    "single": {
        "name": "Single Card Draw",
        "positions": ["Present Situation"],
        "description": "A quick insight into your current situation or question"
    },
    "three": {
        "name": "Past-Present-Future",
        "positions": ["Past", "Present", "Future"],
        "description": "Understanding your journey through time"
    },
    "situation": {
        "name": "Situation Analysis",
        "positions": ["You", "Challenge", "Advice", "Outcome"],
        "description": "Deep dive into a specific situation"
    },
    "relationship": {
        "name": "Relationship Spread",
        "positions": ["You", "The Other", "The Connection", "Challenges", "Potential"],
        "description": "Understanding relationship dynamics"
    },
    "celtic": {
        "name": "Celtic Cross",
        "positions": [
            "Present", "Challenge", "Past", "Future", 
            "Above (Goals)", "Below (Foundation)", "Advice", 
            "External Influences", "Hopes and Fears", "Outcome"
        ],
        "description": "Comprehensive reading of your situation"
    }
}

def draw_cards(num_cards: int) -> List[Tuple[str, str]]:
    """
    Draw random cards from the tarot deck
    Returns list of (card_name, meaning) tuples
    """
    deck_items = list(TAROT_DECK.items())
    random.shuffle(deck_items)
    return deck_items[:num_cards]

def generate_spread(name: str, spread_type: str) -> dict:
    """
    Generate a tarot spread based on type
    PRESERVED - Core tarot reading logic
    """
    if spread_type not in SPREAD_TYPES:
        spread_type = "three"  # Default fallback
    
    spread_info = SPREAD_TYPES[spread_type]
    num_cards = len(spread_info["positions"])
    
    # Draw cards
    drawn_cards = draw_cards(num_cards)
    
    # Build card positions
    cards = []
    for i, (card_name, card_meaning) in enumerate(drawn_cards):
        position = spread_info["positions"][i]
        cards.append({
            "position": position,
            "card": card_name,
            "meaning": card_meaning,
            "position_number": i + 1
        })
    
    # Build basic interpretations
    interpretations = []
    for card_info in cards:
        interpretation = f"{card_info['position']}: {card_info['card']} - {card_info['meaning']}"
        interpretations.append(interpretation)
    
    return {
        "spread_name": spread_info["name"],
        "spread_description": spread_info["description"],
        "cards": cards,
        "interpretations": interpretations,
        "querent": name
    }

def generate_summary(name: str, cards_output: str, dream: str = None) -> dict:
    """
    Generate AI-enhanced tarot summary with fallback support
    ENHANCED - Now uses LLM Gateway with OpenAI → Groq fallback
    """
    
    async def _generate():
        # Build comprehensive prompt
        prompt = f"""Tarot Reading for {name}

Cards Drawn:
{cards_output}"""
        
        if dream:
            prompt += f"""

Dream Context:
{dream}

Please integrate the dream symbolism with the tarot reading for deeper insight."""
        
        prompt += """

Provide a comprehensive, insightful tarot reading that:
1. Synthesizes the meaning of all cards drawn
2. Weaves them into a cohesive narrative
3. Offers specific, actionable guidance
4. Maintains a compassionate, empowering tone
5. Addresses both challenges and opportunities

If dream context is provided, explore the connection between dream symbols and card meanings.

Write 4-6 paragraphs with depth and nuance."""
        
        messages = [
            {
                "role": "system",
                "content": "You are a gifted tarot reader with deep knowledge of symbolism, psychology, and spirituality. You provide profound, compassionate insights that empower and guide. Your readings blend intuitive wisdom with practical guidance."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            result = await llm_gateway.chat_completion(
                messages=messages,
                temperature=0.8,
                max_tokens=800,
                module_type="tarot_reading",
                use_tools=False
            )
            
            if result["success"]:
                summary_text = result["content"]
                provider_used = result["provider"]
                
                return {
                    "summary": summary_text,
                    "provider": provider_used,
                    "enhanced": True,
                    "querent": name
                }
            else:
                # AI failed - return basic interpretation
                print(f" Tarot AI enhancement failed: {result.get('error')}")
                return {
                    "summary": get_basic_tarot_summary(cards_output),
                    "provider": "fallback",
                    "enhanced": False,
                    "querent": name
                }
                
        except Exception as e:
            print(f"Error generating tarot summary: {e}")
            return {
                "summary": get_basic_tarot_summary(cards_output),
                "provider": "error_fallback",
                "enhanced": False,
                "querent": name
            }
    
    # Run async function synchronously
    try:
        return asyncio.run(_generate())
    except Exception as e:
        print(f"Critical error in tarot summary: {e}")
        return {
            "summary": get_basic_tarot_summary(cards_output),
            "provider": "critical_error",
            "enhanced": False,
            "querent": name
        }

def get_basic_tarot_summary(cards_output: str) -> str:
    """
    Fallback summary when AI is unavailable
    Provides meaningful interpretation without AI
    """
    return f"""Your tarot reading reveals important insights for your journey.

{cards_output}

The cards suggest a time of reflection and growth. Pay attention to the energies each card represents - they offer guidance for navigating your current situation. Trust your intuition as you interpret these messages in the context of your life.

The cards remind you that you have the inner wisdom and strength to face whatever lies ahead. Each card is a mirror reflecting aspects of your journey, inviting you to look deeper and understand the patterns at play.

Consider journaling about which cards resonate most strongly with you, and what actions or changes they might be encouraging you to explore."""

def get_card_meanings_by_suit(suit: str = None) -> dict:
    """
    Get all cards of a specific suit or all cards
    Useful for educational purposes
    """
    if suit:
        return {k: v for k, v in TAROT_DECK.items() if suit.lower() in k.lower()}
    return TAROT_DECK

def get_major_arcana() -> dict:
    """Get only Major Arcana cards"""
    major_arcana = ["Fool", "Magician", "High Priestess", "Empress", "Emperor", 
                    "Hierophant", "Lovers", "Chariot", "Strength", "Hermit",
                    "Wheel of Fortune", "Justice", "Hanged Man", "Death", 
                    "Temperance", "Devil", "Tower", "Star", "Moon", "Sun", 
                    "Judgement", "World"]
    
    return {k: v for k, v in TAROT_DECK.items() 
            if any(arcana in k for arcana in major_arcana)}

def get_daily_card() -> dict:
    """
    Draw a single card for daily guidance
    """
    card_name, card_meaning = random.choice(list(TAROT_DECK.items()))
    return {
        "card": card_name,
        "meaning": card_meaning,
        "daily_guidance": f"Today, {card_name} suggests: {card_meaning}"
    }