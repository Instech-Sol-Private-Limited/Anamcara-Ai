import spacy
import json
from typing import List, Dict, Any
import json
import re
import os
from dotenv import load_dotenv  
from openai import OpenAI
from app.services.llm_gateway import llm_gateway

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


async def enhance_matches_with_ai(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enhance match data with AI-generated insights using LLM Gateway with fallback.
    Provides detailed compatibility analysis including traits, synergies, and icebreakers.
    """
    try:
        enhanced_matches = []
        
        for match in matches:
            try:
                user_profile = match.get("data", {})  # User's own profile
                other_profile = match.get("data", {})  # Match's profile
                
                # If there's a nested structure, adjust accordingly
                if "user_data" in match:
                    user_profile = match.get("user_data", {})
                if "other_user_data" in match:
                    other_profile = match.get("other_user_data", {})
                
                # Create detailed prompt for AI analysis
                prompt = f"""Analyze these two user profiles for a friendship matching app and provide detailed compatibility insights.

User 1 Profile:
- Kind of connection: {user_profile.get('kind_connection', [])}
- Social energy: {user_profile.get('social_energy_feel_most', [])}
- Favorite conversations: {user_profile.get('favorite_conversations_light_up', [])}
- Hobbies: {user_profile.get('happiest_hobbies', [])}
- Must-haves: {user_profile.get('top_must_haves_to_match_you', [])}
- Deal breakers: {user_profile.get('deal_breakers', [])}
- Self description: {user_profile.get('self_words', [])}
- Clicks best with: {user_profile.get('click_best_with', [])}
- Care language: {user_profile.get('care_language', [])}
- Conflict style: {user_profile.get('conflict_style_handle', [])}
- Non-negotiables: {user_profile.get('non_negotiable_friend', [])}

User 2 Profile (Match):
- Name: {match.get('name', 'Unknown')}
- Kind of connection: {other_profile.get('kind_connection', [])}
- Social energy: {other_profile.get('social_energy_feel_most', [])}
- Favorite conversations: {other_profile.get('favorite_conversations_light_up', [])}
- Hobbies: {other_profile.get('happiest_hobbies', [])}
- Must-haves: {other_profile.get('top_must_haves_to_match_you', [])}
- Deal breakers: {other_profile.get('deal_breakers', [])}
- Self description: {other_profile.get('self_words', [])}
- Clicks best with: {other_profile.get('click_best_with', [])}
- Care language: {other_profile.get('care_language', [])}
- Conflict style: {other_profile.get('conflict_style_handle', [])}
- Non-negotiables: {other_profile.get('non_negotiable_friend', [])}

Compatibility Score: {match.get('percent_match', 0)}%

Please provide a JSON response with the following structure:
{{
    "sharedInterests": [list 3-5 specific shared interests or activities],
    "traits": [list 3-4 key personality traits of the match],
    "synergies": [list 3 specific reasons why they would connect well],
    "cautionFlags": [list 2-3 potential areas where they might need to compromise or understand differences],
    "icebreakers": [list 3 personalized conversation starters based on their shared interests]
}}

Make the response natural, specific, and personalized based on their actual profile data. Use "you" when referring to the matched person. Return ONLY the JSON object, no additional text."""

                messages = [
                    {
                        "role": "system",
                        "content": "You are a friendship compatibility expert who analyzes user profiles and provides insightful, personalized compatibility analysis. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
                
                # Use LLM Gateway with fallback (OpenAI → Groq)
                result = await llm_gateway.chat_completion(
                    messages=messages,
                    temperature=0.4,
                    max_tokens=1500,
                    module_type="dream_analysis",
                    use_tools=False
                )
                
                if result["success"]:
                    ai_response = result["content"]
                    
                    # Try to extract and parse JSON
                    try:
                        # Clean the response and parse JSON
                        ai_response = ai_response.strip()
                        # Remove markdown code blocks if present
                        ai_response = re.sub(r'^```json\s*', '', ai_response)
                        ai_response = re.sub(r'\s*```$', '', ai_response)
                        
                        ai_insights = json.loads(ai_response)
                        
                    except json.JSONDecodeError:
                        # Try to find JSON in the response
                        json_match = re.search(r'\{[\s\S]*\}', ai_response)
                        if json_match:
                            try:
                                ai_insights = json.loads(json_match.group())
                            except:
                                # Ultimate fallback
                                ai_insights = get_fallback_insights()
                        else:
                            ai_insights = get_fallback_insights()
                else:
                    # LLM Gateway failed (all providers down)
                    print(f"⚠️ AI enhancement failed for {match.get('name')}: {result.get('error')}")
                    ai_insights = get_fallback_insights()
                
                # Build enhanced match object
                enhanced_match = {
                    "id": match.get("match_id"),
                    "name": match.get("name", "Unknown"),
                    "age": match.get("age"),
                    "avatar": match.get("avatar", "/api/placeholder/150/150"),
                    "compatibility": match.get("percent_match", 0),
                    "sharedInterests": ai_insights.get("sharedInterests", []),
                    "traits": ai_insights.get("traits", []),
                    "synergies": ai_insights.get("synergies", []),
                    "cautionFlags": ai_insights.get("cautionFlags", []),
                    "icebreakers": ai_insights.get("icebreakers", []),
                    "ai_provider": result.get("provider", "fallback") if result["success"] else "fallback"
                }
                
                enhanced_matches.append(enhanced_match)
                
            except Exception as e:
                # Error processing individual match - add with fallback data
                print(f"Error processing match {match.get('name', 'Unknown')}: {e}")
                enhanced_matches.append({
                    "id": match.get("match_id"),
                    "name": match.get("name", "Unknown"),
                    "age": match.get("age"),
                    "avatar": match.get("avatar", "/api/placeholder/150/150"),
                    "compatibility": match.get("percent_match", 0),
                    "sharedInterests": ["Common interests"],
                    "traits": ["Friendly", "Open-minded"],
                    "synergies": ["Compatible values"],
                    "cautionFlags": ["Get to know each other's communication styles"],
                    "icebreakers": ["Tell me about your favorite hobbies!"],
                    "ai_provider": "error_fallback"
                })
        
        return enhanced_matches
        
    except Exception as e:
        # Critical error - return basic matches without AI enhancement
        print(f"Critical error in enhance_matches_with_ai: {e}")
        return [{
            "id": m.get("match_id"),
            "name": m.get("name", "Unknown"),
            "age": m.get("age"),
            "avatar": m.get("avatar", "/api/placeholder/150/150"),
            "compatibility": m.get("percent_match", 0),
            "sharedInterests": [],
            "traits": [],
            "synergies": [],
            "cautionFlags": [],
            "icebreakers": [],
            "ai_provider": "critical_error"
        } for m in matches]


def get_fallback_insights() -> Dict[str, List[str]]:
    """
    Provide generic but meaningful fallback insights when AI fails
    """
    return {
        "sharedInterests": [
            "Common values and interests",
            "Similar outlook on friendships",
            "Compatible social preferences"
        ],
        "traits": [
            "Friendly and approachable",
            "Open to new connections",
            "Values meaningful relationships",
            "Good communication skills"
        ],
        "synergies": [
            "High compatibility score indicates aligned values",
            "Similar approaches to building friendships",
            "Complementary personality traits"
        ],
        "cautionFlags": [
            "Take time to understand each other's communication styles",
            "Be open about preferences and boundaries",
            "Allow the friendship to develop naturally"
        ],
        "icebreakers": [
            "What drew you to join this community?",
            "Tell me about something you're passionate about!",
            "What's your ideal way to spend a weekend?",
            "What kind of conversations do you enjoy most?"
        ]
    }