# models/schemas.py
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
from typing import List, Optional, Dict
from enum import Enum

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



# ==================== ENUMS ====================

class TestStatus(str, Enum):
    GENERATED = "generated"
    STARTED = "started"
    SUBMITTED = "submitted"
    EXPIRED = "expired"

class ChallengeMode(str, Enum):
    ONE_V_ONE = "1v1"
    ONE_V_ONE_AI = "1v1_ai"
    TWO_V_TWO = "2v2"
    TEAM = "team"

class ChallengeStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    ACTIVE = "active"
    FINISHED = "finished"
    EXPIRED = "expired"

# ==================== TEST MODELS ====================

class MCQOption(BaseModel):
    A: str
    B: str
    C: str
    D: str
    E: Optional[str] = None  # For personality tests with 5 options

class MCQQuestion(BaseModel):
    question_id: int
    question: str
    options: MCQOption

class GenerateTestRequest(BaseModel):
    subject: str = Field(..., description="Test subject (e.g., IQ Test, EQ Test)")
    student_name: str = Field(..., min_length=2, max_length=100)
    student_email: Optional[str] = Field(None, description="Optional email for history tracking")

class GenerateTestResponse(BaseModel):
    test_id: str
    subject: str
    student_name: str
    questions: List[MCQQuestion]
    status: TestStatus
    message: Optional[str] = None

class StartTestRequest(BaseModel):
    test_id: str

class StartTestResponse(BaseModel):
    test_id: str
    start_time: datetime
    end_time: datetime
    time_remaining_seconds: int
    message: str

class SubmitAnswer(BaseModel):
    question_id: int
    selected_answer: str = Field(..., pattern="^[A-E]$", description="Selected option (A, B, C, D, or E)")

class SubmitTestRequest(BaseModel):
    test_id: str
    answers: List[SubmitAnswer]

class QuestionResult(BaseModel):
    question_id: int
    question: str
    selected_answer: str
    correct_answer: str
    is_correct: bool

class SubmitTestResponse(BaseModel):
    test_id: str
    score: int
    total_questions: int
    percentage: float
    time_taken_seconds: int
    results: List[QuestionResult]
    status: TestStatus

# ==================== CHALLENGE MODELS ====================

class ChallengeRequest(BaseModel):
    subject: str = Field(..., description="Challenge subject")
    mode: ChallengeMode
    team_size: int = Field(1, ge=1, le=5, description="Players per team (1-5)")
    created_by: str = Field(..., description="User ID of creator")
    duration_minutes: int = Field(10, ge=5, le=30, description="Challenge duration (5-30 minutes)")

class ChallengeJoinRequest(BaseModel):
    challenge_id: str
    user_id: str
    team: int = Field(..., ge=1, le=2, description="Team number (1 or 2)")

class ChallengeSubmitRequest(BaseModel):
    challenge_id: str
    user_id: str
    answers: Dict[str, str] = Field(..., description="Question ID to answer mapping")

class ParticipantInfo(BaseModel):
    user_id: str
    team: int
    score: int
    finished: bool
    joined_at: str

class TeamScore(BaseModel):
    total_score: int
    members: List[Dict]

class ChallengeResultsResponse(BaseModel):
    challenge_id: str
    subject: str
    mode: str
    status: str
    winner: Optional[str]
    team_scores: Dict[int, TeamScore]
    started_at: Optional[str]
    finished_at: Optional[str]

class ChallengeStatusResponse(BaseModel):
    challenge_id: str
    status: str
    subject: str
    mode: str
    time_remaining_seconds: Optional[int]
    participants_count: int
    participants_finished: int
    started_at: Optional[str]
    ends_at: Optional[str]

# ==================== RESPONSE MODELS ====================

class TestHistoryItem(BaseModel):
    test_id: str
    subject: str
    status: str
    created_at: str
    retake_number: int
    score: Optional[int]
    percentage: Optional[float]

class TestHistoryResponse(BaseModel):
    student_email: str
    test_history: List[TestHistoryItem]

class ChallengeListItem(BaseModel):
    challenge_id: str
    subject: str
    mode: str
    status: str
    team_size: int
    created_by: str
    participants_count: int
    created_at: str

class ActiveChallengesResponse(BaseModel):
    challenges: List[ChallengeListItem]

class UserChallengeItem(BaseModel):
    challenge_id: str
    subject: str
    mode: str
    status: str
    user_score: int
    user_finished: bool
    created_at: str

class UserChallengesResponse(BaseModel):
    user_id: str
    challenges: List[UserChallengeItem]

# ==================== DATABASE MODELS ====================

class TestDB(BaseModel):
    """Database model for tests table"""
    test_id: str
    subject: str
    student_name: str
    student_email: Optional[str]
    status: str
    created_at: str
    start_time: Optional[str]
    end_time: Optional[str]
    submitted_at: Optional[str]
    questions_data: List[Dict]
    retake_of: Optional[str] = None
    retake_number: int = 0

class SubmissionDB(BaseModel):
    """Database model for submissions table"""
    test_id: str
    submitted_answers: List[Dict]
    score: int
    total_questions: int
    percentage: float
    time_taken_seconds: int
    submitted_at: str

class ChallengeDB(BaseModel):
    """Database model for challenges table"""
    id: str
    subject: str
    mode: str
    team_size: int
    created_by: str
    status: str
    duration_minutes: int
    test_id: Optional[str]
    created_at: str
    started_at: Optional[str]
    ends_at: Optional[str]
    finished_at: Optional[str]

class ChallengeParticipantDB(BaseModel):
    """Database model for challenge_participants table"""
    challenge_id: str
    user_id: str
    team: int
    score: int
    finished: bool
    answers: Optional[Dict[str, str]]
    joined_at: str
    finished_at: Optional[str]

class QueryRequest(BaseModel):
    user_id: Optional[str] = None
    query: str
    user_type: str = "guest"
    conversation_id: Optional[str] = None  # ✅ NEW: Track conversation thread

class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: str

class QueryResponse(BaseModel):
    message: str
    safety: str = "ok"
    conversation_id: Optional[str] = None
    chat_history: Optional[List[Message]] = None  # ✅ NEW: Return history
