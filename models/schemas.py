from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class PersonalityTrait(BaseModel):
    name: str
    description: Optional[str] = None

class PersonaCreate(BaseModel):
    name: str
    gender: str
    personality_traits: List[str]
    user_id: str

class PersonaResponse(BaseModel):
    id: str
    name: str
    gender: str
    personality_traits: List[str]
    user_id: str
    created_at: datetime
    thread_id: str
    
class ChatMessageEntry(BaseModel):
    sender: str  # "user" or "ai"
    message: str
    timestamp: datetime

class ChatThread(BaseModel):
    thread_id: str
    persona_id: str
    messages: List[ChatMessageEntry]

class UserChatDocument(BaseModel):
    user_id: str
    threads: List[ChatThread]

class ChatMessage(BaseModel):
    message: str
    persona_id: str
    thread_id: str

class ChatResponse(BaseModel):
    response: str
    thread_id: str
    persona_id: str
    timestamp: datetime

class MoodCheckIn(BaseModel):
    persona_id: str
    mood: str
    description: Optional[str] = None

class MoodResponse(BaseModel):
    response: str
    persona_id: str
    timestamp: datetime

class UserFormData(BaseModel):
    user_id: str
    kind_connection: List[str]  # So… what kind of connection are you hoping to find here?
    social_energy_feel_most: List[str]    # When it comes to social energy, which feels most like you?
    favorite_conversations_light_up: List[str]  # What kind of conversations make you light up?
    happiest_hobbies: List[str]  # Which activities or hobbies make you happiest?
    top_must_haves_to_match_you: List[str]    # If you had to name your top 3 must-haves in someone, what would they be?
    deal_breakers: List[str]     # And on the flip side… what’s a deal-breaker for you?
    self_words: List[str]        # Which words feel like “you” the most?
    click_best_with: List[str]         # You usually click best with
    care_language: List[str]           # When someone cares about you, how do you like them to show it?
    conflict_style_handle: List[str]          # If you and someone disagree, how do you usually handle it?
    non_negotiable_friend: List[str]          # Finally… what’s non-negotiable for you in a friend or partner?
