# models/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid
from typing import List

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
    last_interaction: Optional[datetime] = None
    
class ChatMessageEntry(BaseModel):
    id: Optional[str] = None
    thread_id: str
    persona_id: str
    user_id: str
    sender: str  # "user" or "ai"
    message: str
    timestamp: datetime

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
    kind_connection: List[str] = Field(default_factory=list)
    social_energy_feel_most: List[str] = Field(default_factory=list)
    favorite_conversations_light_up: List[str] = Field(default_factory=list)
    happiest_hobbies: List[str] = Field(default_factory=list)
    top_must_haves_to_match_you: List[str] = Field(default_factory=list)
    deal_breakers: List[str] = Field(default_factory=list)
    self_words: List[str] = Field(default_factory=list)
    click_best_with: List[str] = Field(default_factory=list)
    care_language: List[str] = Field(default_factory=list)
    conflict_style_handle: List[str] = Field(default_factory=list)
    non_negotiable_friend: List[str] = Field(default_factory=list)

class DailyMessage(BaseModel):
    id: Optional[str] = None
    persona_id: str
    message: str
    type: str = "daily_greeting"
    delivered: bool = False
    timestamp: datetime