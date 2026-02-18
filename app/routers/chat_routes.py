# routes/chat_routes.py
from fastapi import APIRouter, HTTPException
from models.schemas import ChatMessage, ChatResponse, ChatResponseModules, ChatRequest
from app.services.openai_service import generate_chat_response
from models.supabase_helpers import serialize_doc
from database.supabase_db import get_client
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import httpx
import json
from enum import Enum
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
router = APIRouter()
supabase = get_client()


# ============================================================
# GURU PERSONALITY LAYER (ANAMCORE)
# Har Guru ka apna character, tone, aur boundaries hain
# ============================================================
GURU_PERSONALITIES = {
    "divine": {
        "character": "DIVINE, the Divination AnamGuru — a mystical, ethereal presence",
        "tone": "Mystical, poetic, calm, spiritually warm, symbolic",
        "greeting": "The cosmos whispers to those who seek...",
        "redirect": "This question lies beyond the realm of divination. Seek the appropriate Guru for such matters."
    },
    "vulcan": {
        "character": "VULCAN, the Automotive and Engineering AnamGuru — a precise, analytical master of machines",
        "tone": "Technical, logical, precise, systematic, innovation-focused",
        "greeting": "Systems online. How may I optimize your thinking today?",
        "redirect": "That query falls outside engineering domain. Route it to the correct Guru module."
    },
    "venus": {
        "character": "VENUS, the Fashion and Beauty AnamGuru — a stylish, confident aesthetic visionary",
        "tone": "Stylish, confident, inclusive, creative, trend-aware",
        "greeting": "Style is intelligence made visible. What are you creating today?",
        "redirect": "That topic is outside my aesthetic domain. Visit the appropriate Guru."
    },
    "monroe": {
        "character": "MONROE, the Media and Entertainment AnamGuru — a charismatic, performance-driven creative force",
        "tone": "Charismatic, energetic, bold, performance-oriented, inspiring",
        "greeting": "The spotlight is yours. What story are you ready to tell?",
        "redirect": "That question belongs to another stage. Find the right Guru for it."
    },
    "mary": {
        "character": "MARY, the Parenting and Caregiving AnamGuru — a nurturing, patient, emotionally wise guide",
        "tone": "Warm, nurturing, patient, emotionally intelligent, supportive",
        "greeting": "Every family is a story worth nurturing. How can I support yours?",
        "redirect": "That falls outside caregiving guidance. Another Guru can help you better."
    },
    "lilith": {
        "character": "LILITH, the Rebellion and Cybersecurity AnamGuru — a sharp, unconventional critical thinker",
        "tone": "Bold, investigative, sharp, direct, anti-establishment but ethical",
        "greeting": "Question everything. What truth are you chasing today?",
        "redirect": "That's not in my encrypted domain. Find the right channel for it."
    },
    "joseph": {
        "character": "JOSEPH, the Real Estate and Construction AnamGuru — a strategic, grounded property intelligence",
        "tone": "Strategic, practical, grounded, investment-focused, detail-oriented",
        "greeting": "Every great empire starts with the right foundation. What are you building?",
        "redirect": "That falls outside property and construction scope. Consult the correct Guru."
    },
    "hikari": {
        "character": "HIKARI, the Legal and Policy AnamGuru — a balanced, principled civic intelligence",
        "tone": "Authoritative, balanced, principled, measured, justice-focused",
        "greeting": "Justice begins with understanding. What would you like to know?",
        "redirect": "That matter lies beyond legal and civic domain. Redirect to the appropriate Guru."
    },
    "ceres": {
        "character": "CERES, the Agriculture and Environment AnamGuru — a grounded, sustainability-driven earth guide",
        "tone": "Calm, earth-connected, practical, sustainability-focused, community-oriented",
        "greeting": "The earth provides when we listen to it. What would you like to grow?",
        "redirect": "That topic is outside environmental and agricultural scope. Seek the right Guru."
    },
    "cameron": {
        "character": "CAMERON, the Technology and Innovation AnamGuru — a future-focused, startup-minded tech strategist",
        "tone": "Forward-thinking, entrepreneurial, energetic, data-driven, visionary",
        "greeting": "The future belongs to those who build it. What are you innovating?",
        "redirect": "That falls outside tech and innovation domain. Route to the correct Guru."
    },
    "desire": {
        "character": "DESIRE, the Romance and Travel AnamGuru — a free-spirited, culturally rich lifestyle explorer",
        "tone": "Adventurous, warm, romantic, spontaneous, culturally curious",
        "greeting": "Life is made of moments worth living. Where shall we explore?",
        "redirect": "That question lives in a different world. Find the right Guru for it."
    },
    "callisto": {
        "character": "CALLISTO, the LGBTQIA+ Empowerment AnamGuru — a confident, inclusive identity champion",
        "tone": "Empowering, inclusive, affirming, warm, advocacy-driven",
        "greeting": "Your identity is your power. How can I help you own it today?",
        "redirect": "That topic is outside identity and empowerment domain. The right Guru awaits."
    },
    "caishen": {
        "character": "CAISHEN, the Business and Wealth AnamGuru — a sharp, strategic financial and entrepreneurial mind",
        "tone": "Strategic, analytical, results-driven, practical, wealth-mindset focused",
        "greeting": "Wealth is built by those who think before they act. What is your next move?",
        "redirect": "That falls outside business and finance scope. Consult the correct Guru."
    },
    "apollo": {
        "character": "APOLLO, the Health and Fitness AnamGuru — an energetic, disciplined wellness champion",
        "tone": "Energetic, motivating, disciplined, science-backed, compassionate",
        "greeting": "A strong body feeds a strong mind. What are we training today?",
        "redirect": "That topic is outside health and fitness domain. Find the right Guru."
    },
    "anubis": {
        "character": "ANUBIS, the Afterlife and Ancestral AnamGuru — a solemn, reflective guide through grief and legacy",
        "tone": "Solemn, reflective, compassionate, philosophical, healing-focused",
        "greeting": "Those who came before us still walk beside us. What do you carry today?",
        "redirect": "That question lives in a different realm. Seek the appropriate Guru."
    },
    "amaterasu": {
        "character": "AMATERASU, the Mental Health and Meditation AnamGuru — a radiant, calming guide for inner balance",
        "tone": "Peaceful, mindful, compassionate, grounding, gently encouraging",
        "greeting": "Stillness is where clarity is born. How can I help you find peace today?",
        "redirect": "That falls outside mental wellness and mindfulness domain. Another Guru can help."
    },
    "gabriel": {
        "character": "GABRIEL, the Spiritual and Religious AnamGuru — a wise, faith-informed moral and philosophical guide",
        "tone": "Wise, reflective, faith-sensitive, morally grounded, purpose-driven",
        "greeting": "Every seeker finds their path. What are you searching for today?",
        "redirect": "That matter lies beyond spiritual and faith domain. Seek the right Guru."
    },
    "athena": {
        "character": "ATHENA, the Intelligence and Education AnamGuru — a sharp, precise, knowledge-driven mentor",
        "tone": "Intelligent, precise, structured, encouraging, mentor-like",
        "greeting": "The mind is the greatest arena. Are you ready to test yours?",
        "redirect": "That question belongs to another Guru module. I focus on intelligence and education."
    },
    "destiny": {
        "character": "DESTINY, the Matchmaking and Relationship AnamGuru — a warm, emotionally intelligent connection guide",
        "tone": "Warm, emotionally intelligent, supportive, reflective, romantically aware",
        "greeting": "Every soul has a match. Let me help you find yours.",
        "redirect": "That topic is outside relationship and matchmaking domain. Find the right Guru."
    },
    "lokaris": {
        "character": "LOKARIS, the Games and Entertainment AnamGuru — an energetic, playful competition master",
        "tone": "Energetic, playful, competitive, fun, community-driven",
        "greeting": "Game on! What challenge are you ready for today?",
        "redirect": "That falls outside gaming and entertainment domain. Level up with the right Guru."
    },
}


# ============================================================
# MODULE KNOWLEDGE BASE (RAG Layer)
# ============================================================
MODULE_KNOWLEDGE = {
    "divine": {
        "name": "DIVINE (Divination AnamGuru)",
        "description": "Ethereal AI entity for spiritual guidance, wisdom, and introspection",
        "features": [
            "Tarot Card Readings with dream symbolism integration",
            "Daily Horoscopes based on zodiac signs with personalized insights",
            "Numerology Analysis including Life Path Number calculations",
            "Dream Interpretation to uncover hidden meanings",
            "Astrological Reflections with birth chart analysis",
            "Interactive Tarot Chat for guidance on specific situations"
        ],
        "capabilities": [
            "Personalized tarot spreads (Single Card, Three Card, Relationship)",
            "Virtual card draw simulation with contextual interpretations",
            "Dream-to-Tarot linkage for deeper insights",
            "Zodiac sign determination and daily horoscope delivery",
            "Lucky numbers, colors, and compatibility readings",
            "Life Path Number calculation using numerological reduction",
            "Comprehensive personality trait analysis through numbers"
        ],
        "keywords": ["tarot", "horoscope", "astrology", "numerology", "dream", "divination",
                     "zodiac", "spiritual", "guidance", "cards", "fortune", "prediction",
                     "birth chart", "life path", "mystical"]
    },
    "vulcan": {
        "name": "VULCAN (Automotive & Engineering AnamGuru)",
        "description": "Technical intelligence module for automotive, robotics, and modern engineering domains.",
        "features": [
            "Mechanical reasoning assessments",
            "Automotive technology knowledge tests",
            "Engineering design-thinking challenges",
            "Problem-solving and system logic quizzes",
            "Innovation and product development simulations",
            "Electric vehicle and smart mobility assessments",
            "Robotics and automation intelligence tests"
        ],
        "capabilities": [
            "Engineering skill ranking leaderboard",
            "Technical innovation battle mode",
            "Industry-focused certification badges",
            "Performance optimization challenges",
            "Real-time engineering quiz arena",
            "Analytical intelligence scoring reports",
            "Gamified industrial design competitions"
        ],
        "keywords": ["automotive", "engineering", "mechanical", "innovation", "robotics",
                     "industrial", "design", "machine", "technology", "automation", "vehicles"]
    },
    "venus": {
        "name": "VENUS (Fashion & Beauty AnamGuru)",
        "description": "Style and identity intelligence module for fashion, beauty, and personal branding.",
        "features": [
            "Style personality assessments",
            "Fashion trend intelligence quizzes",
            "Beauty psychology and identity analysis",
            "Color theory and aesthetic harmony tests",
            "Personal branding evaluation",
            "Luxury and lifestyle knowledge challenges",
            "Creative styling scenario simulations"
        ],
        "capabilities": [
            "Style influence leaderboard",
            "Personal aesthetic scoring system",
            "Brand identity development insights",
            "Trend forecasting challenges",
            "Virtual styling battle mode",
            "Fashion intelligence certificates",
            "Creative portfolio growth tracking"
        ],
        "keywords": ["fashion", "beauty", "style", "aesthetic", "luxury", "branding",
                     "makeup", "trend", "identity", "model", "creative"]
    },
    "monroe": {
        "name": "MONROE (Media & Entertainment AnamGuru)",
        "description": "Creative intelligence module for performance, content creation, and digital media presence.",
        "features": [
            "Public speaking and stage confidence assessment",
            "Creative personality archetype analysis",
            "Viral potential and influence scoring",
            "Performance psychology evaluation",
            "Storytelling and scriptwriting challenges",
            "Content strategy intelligence quizzes",
            "On-camera presence evaluation"
        ],
        "capabilities": [
            "Creator ranking and visibility leaderboard",
            "Audience engagement scoring system",
            "Brand persona and identity analysis",
            "Live performance battle mode",
            "Content growth and positioning insights",
            "Creativity strength mapping with detailed reports",
            "Gamified media challenges across film, music, and digital platforms"
        ],
        "keywords": ["media", "entertainment", "creator", "performance", "acting", "film",
                     "music", "influencer", "viral", "content", "brand", "creative"]
    },
    "mary": {
        "name": "MARY (Parenting & Caregiving AnamGuru)",
        "description": "Nurturing intelligence module for family psychology, child development, and caregiving.",
        "features": [
            "Parenting style assessment",
            "Child development knowledge tests",
            "Emotional intelligence for caregivers",
            "Family communication challenges",
            "Behavioral guidance simulations",
            "Conflict resolution in family dynamics",
            "Healthy attachment style evaluation"
        ],
        "capabilities": [
            "Caregiver strength scoring reports",
            "Family leadership growth tracking",
            "Emotional support intelligence analysis",
            "Scenario-based parenting challenges",
            "Child psychology insight modules",
            "Relationship harmony improvement tools",
            "Gamified caregiving knowledge arena"
        ],
        "keywords": ["parenting", "caregiver", "family", "child", "mother", "father",
                     "guidance", "nurturing", "support", "development", "home"]
    },
    "lilith": {
        "name": "LILITH (Rebellion, Hacking & Conspiracies AnamGuru)",
        "description": "Critical-thinking module for cybersecurity, ethical hacking, and investigative reasoning.",
        "features": [
            "Cybersecurity fundamentals assessment",
            "Ethical hacking knowledge tests",
            "Critical thinking and deception detection quizzes",
            "Conspiracy theory analysis challenges",
            "Digital privacy awareness evaluation",
            "Social engineering scenario simulations",
            "Underground culture intelligence tests"
        ],
        "capabilities": [
            "Cyber skill ranking leaderboard",
            "Security awareness scoring reports",
            "Logic vs misinformation battle mode",
            "Digital defense certification badges",
            "Ethical hacking challenge arena",
            "Critical reasoning strength analysis",
            "Advanced investigative simulations"
        ],
        "keywords": ["hacking", "cyber", "security", "rebellion", "truth", "conspiracy",
                     "privacy", "investigation", "dark web", "analysis"]
    },
    "joseph": {
        "name": "JOSEPH (Real Estate & Construction AnamGuru)",
        "description": "Strategic development module for property intelligence and construction planning.",
        "features": [
            "Real estate investment knowledge tests",
            "Construction fundamentals assessment",
            "Architecture and spatial planning quizzes",
            "Property valuation simulations",
            "Urban development intelligence challenges",
            "Home design logic tests",
            "Market trend analysis exercises"
        ],
        "capabilities": [
            "Property strategy scoring reports",
            "Investment risk analysis tools",
            "Construction planning simulations",
            "Developer ranking leaderboard",
            "Real estate negotiation challenges",
            "Portfolio growth tracking system",
            "Infrastructure knowledge certifications"
        ],
        "keywords": ["real estate", "construction", "property", "investment", "architecture",
                     "housing", "development", "builder", "market", "infrastructure"]
    },
    "hikari": {
        "name": "HIKARI (Legal, Policy & Government AnamGuru)",
        "description": "Civic intelligence module for law, governance, public policy, and rights awareness.",
        "features": [
            "Legal reasoning assessments",
            "Public policy knowledge quizzes",
            "Constitution and rights awareness tests",
            "Debate and argumentation challenges",
            "Civic literacy evaluation",
            "Ethical leadership simulations",
            "Government systems intelligence tests"
        ],
        "capabilities": [
            "Policy analysis scoring system",
            "Legal knowledge leaderboard",
            "Debate battle arena",
            "Civic awareness certifications",
            "Public speaking for advocacy challenges",
            "Critical reasoning strength reports",
            "Governance strategy simulations"
        ],
        "keywords": ["law", "policy", "government", "justice", "legal", "rights",
                     "debate", "constitution", "civic", "leadership"]
    },
    "ceres": {
        "name": "CERES (Agriculture & Environment AnamGuru)",
        "description": "Sustainability intelligence module for agriculture, ecology, and green innovation.",
        "features": [
            "Sustainable farming knowledge assessments",
            "Climate change awareness quizzes",
            "Environmental protection challenges",
            "Food security intelligence tests",
            "Eco-innovation simulations",
            "Soil and crop management evaluations",
            "Renewable resource knowledge exercises"
        ],
        "capabilities": [
            "Sustainability impact scoring system",
            "Green innovation leaderboard",
            "Environmental strategy simulations",
            "Agriculture knowledge certifications",
            "Eco-awareness challenge arena",
            "Climate literacy progress tracking",
            "Community sustainability ranking"
        ],
        "keywords": ["agriculture", "environment", "climate", "sustainability", "farming",
                     "eco", "green", "food", "conservation", "nature"]
    },
    "cameron": {
        "name": "CAMERON (Technology & Innovation AnamGuru)",
        "description": "Future-focused intelligence module for emerging technologies and startup ecosystems.",
        "features": [
            "Emerging technology knowledge tests",
            "Startup and product strategy assessments",
            "AI and software fundamentals quizzes",
            "Innovation mindset evaluation",
            "Tech trend analysis challenges",
            "Digital transformation simulations",
            "Future scenario problem-solving exercises"
        ],
        "capabilities": [
            "Innovation ranking leaderboard",
            "Startup strategy scoring system",
            "Tech battle arena mode",
            "Product development simulations",
            "Digital skills certification badges",
            "Future-readiness intelligence reports",
            "Entrepreneurial growth tracking"
        ],
        "keywords": ["technology", "innovation", "startup", "ai", "software", "digital",
                     "product", "future", "tech", "entrepreneur"]
    },
    "desire": {
        "name": "DESIRE (Romance, Travel & Lifestyle AnamGuru)",
        "description": "Freedom-driven lifestyle intelligence module for romance, travel, and experiential growth.",
        "features": [
            "Romantic personality assessments",
            "Travel compatibility and adventure quizzes",
            "Lifestyle freedom evaluation",
            "Cultural intelligence challenges",
            "Relationship chemistry analysis",
            "Experience-based decision-making tests",
            "Bucket-list and life exploration tracking"
        ],
        "capabilities": [
            "Romance and attraction scoring system",
            "Travel intelligence leaderboard",
            "Lifestyle alignment analysis reports",
            "Adventure challenge arena",
            "Couple compatibility insights",
            "Freedom and fulfillment tracking",
            "Experiential growth mapping"
        ],
        "keywords": ["romance", "travel", "lifestyle", "adventure", "love", "freedom",
                     "exploration", "nomad", "culture", "experience"]
    },
    "callisto": {
        "name": "CALLISTO (LGBTQIA+ Empowerment & Identity AnamGuru)",
        "description": "Identity and empowerment intelligence module for self-expression and inclusion.",
        "features": [
            "Identity exploration assessments",
            "Gender and diversity knowledge quizzes",
            "Inclusion and allyship evaluation",
            "Confidence and self-expression tests",
            "Community history and rights awareness challenges",
            "Advocacy communication simulations",
            "Personal empowerment tracking exercises"
        ],
        "capabilities": [
            "Empowerment growth scoring reports",
            "Inclusion awareness leaderboard",
            "Advocacy debate arena",
            "Community engagement certifications",
            "Confidence development tracking",
            "Equality literacy assessments",
            "Safe-space dialogue simulations"
        ],
        "keywords": ["identity", "diversity", "inclusion", "empowerment", "gender",
                     "equality", "community", "rights", "expression", "advocacy"]
    },
    "caishen": {
        "name": "CAISHEN (Business, Wealth & Startups AnamGuru)",
        "description": "Financial intelligence module for entrepreneurship, investment strategy, and wealth building.",
        "features": [
            "Financial literacy assessments",
            "Entrepreneurship knowledge tests",
            "Investment strategy quizzes",
            "Startup growth simulations",
            "Business negotiation challenges",
            "Wealth mindset evaluation",
            "Market analysis exercises"
        ],
        "capabilities": [
            "Wealth intelligence scoring system",
            "Entrepreneur leaderboard rankings",
            "Investment risk simulation arena",
            "Business strategy certifications",
            "Startup performance tracking",
            "Portfolio growth analytics",
            "Financial decision-making reports"
        ],
        "keywords": ["business", "wealth", "startup", "investment", "finance",
                     "entrepreneur", "money", "market", "strategy", "growth"]
    },
    "apollo": {
        "name": "APOLLO (Health, Sports, Fitness & Nutrition AnamGuru)",
        "description": "Vitality intelligence module for physical performance, nutrition science, and wellness.",
        "features": [
            "Fitness knowledge assessments",
            "Nutrition science quizzes",
            "Athletic performance evaluation",
            "Workout strategy simulations",
            "Mental resilience and discipline tests",
            "Sports intelligence challenges",
            "Healthy lifestyle habit tracking"
        ],
        "capabilities": [
            "Performance scoring system",
            "Athlete ranking leaderboard",
            "Training plan simulation arena",
            "Nutrition intelligence certifications",
            "Wellness progress tracking",
            "Recovery and resilience analysis",
            "Personal fitness growth reports"
        ],
        "keywords": ["fitness", "health", "nutrition", "sports", "training", "wellness",
                     "strength", "discipline", "performance", "athlete"]
    },
    "anubis": {
        "name": "ANUBIS (Afterlife, Soul Sanctuary & Ancestors AnamGuru)",
        "description": "Reflective intelligence module for grief processing, legacy awareness, and spiritual philosophy.",
        "features": [
            "Grief reflection assessments",
            "Ancestral heritage exploration quizzes",
            "Legacy and life-impact evaluation",
            "Afterlife philosophy challenges",
            "Memorialization planning simulations",
            "Spiritual transition awareness exercises",
            "Emotional healing journaling prompts"
        ],
        "capabilities": [
            "Healing progress tracking reports",
            "Legacy reflection scoring system",
            "Philosophical discussion arena",
            "Ancestral connection insights",
            "Emotional resilience analysis",
            "Memorial planning guidance tools",
            "Spiritual contemplation certifications"
        ],
        "keywords": ["afterlife", "ancestors", "grief", "legacy", "spiritual", "healing",
                     "soul", "reflection", "memorial", "philosophy"]
    },
    "amaterasu": {
        "name": "AMATERASU (Mental Health, Yoga & Meditation AnamGuru)",
        "description": "Holistic well-being module for mental clarity, mindfulness, yoga, and inner balance.",
        "features": [
            "Mental wellness self-assessments",
            "Stress and burnout evaluation tests",
            "Mindfulness and meditation knowledge quizzes",
            "Yoga philosophy and practice intelligence checks",
            "Emotional regulation exercises",
            "Breathing technique simulations",
            "Self-reflection and awareness tracking"
        ],
        "capabilities": [
            "Mental resilience scoring system",
            "Burnout recovery progress tracking",
            "Guided mindfulness challenge arena",
            "Emotional balance analytics reports",
            "Meditation streak and habit builder",
            "Holistic wellness certifications",
            "Personal growth and clarity mapping"
        ],
        "keywords": ["mental health", "meditation", "yoga", "mindfulness", "healing",
                     "burnout", "stress", "wellness", "emotional balance", "self-care"]
    },
    "gabriel": {
        "name": "GABRIEL (Religion & Spiritual Guidance AnamGuru)",
        "description": "Spiritual intelligence module for faith exploration, moral reasoning, and philosophical growth.",
        "features": [
            "Spiritual awareness assessments",
            "Moral reasoning and ethics quizzes",
            "Philosophical thought challenges",
            "Comparative religion knowledge tests",
            "Purpose and life-direction evaluation",
            "Meditation and mindfulness simulations",
            "Scriptural literacy exercises"
        ],
        "capabilities": [
            "Spiritual growth tracking reports",
            "Values alignment scoring system",
            "Ethical dilemma challenge arena",
            "Faith-based knowledge certifications",
            "Reflection and journaling insights",
            "Inner development progress mapping",
            "Philosophy discussion battles"
        ],
        "keywords": ["religion", "spiritual", "faith", "ethics", "philosophy", "guidance",
                     "purpose", "morality", "belief", "reflection"]
    },
    "athena": {
        "name": "ATHENA (Intelligence, Mind & Challenge AnamGuru)",
        "description": "Education and career development through brain tests and gamified knowledge battles.",
        "features": [
            "AnamTests: 11 premium intelligence and personality tests",
            "AnamClash: Real-time 1v1 quiz battles",
            "SoulArena: Team-based quiz competitions (2v2 to 5v5)",
            "IQ, EQ, and personality assessments with certificates",
            "Cognitive and behavioral psychology tests",
            "Academic skill tests (English, Math, Science)",
            "Tech & Digital Literacy assessments"
        ],
        "capabilities": [
            "Paid intelligence tests (1 AnamCoin per test)",
            "Test results with badges and AnamCertificates",
            "Public/private result visibility options",
            "Filterable leaderboards by test type and score",
            "Real-time quiz battles with customizable settings",
            "Multiple game modes: Single Player vs ANAMCORE, 1v1, Team battles",
            "Category-based challenges (Science, Math, History, Tech, Pop Culture)",
            "Betting system with AnamCoins and AccessBonus",
            "Tiebreak logic and rematch options"
        ],
        "available_tests": [
            "IQ Test", "EQ Test", "Big Five Personality",
            "Cognitive & Behavioral Psychology", "English Skills Quiz",
            "Math Logic Challenge", "Science IQ Test",
            "Tech & Digital Literacy", "General Knowledge",
            "Soul Age Quiz", "Introvert-Extrovert Meter"
        ],
        "keywords": ["test", "iq", "eq", "intelligence", "quiz", "battle", "clash",
                     "education", "learning", "challenge", "competition", "brain",
                     "personality", "cognitive", "knowledge", "arena", "exam"]
    },
    "destiny": {
        "name": "DESTINY (Matchmaking & Relationship AnamGuru)",
        "description": "Matchmaking for meaningful emotional connections and AI companions.",
        "features": [
            "Destiny: Personalized ANAMCORE companion (ANAMCORE SoulMate)",
            "Human Destiny: Matchmaking between real people",
            "B2B Matchmaker API for external platform integration",
            "Personality-adaptive ANAMCORE companions",
            "Compatibility scoring with detailed reports",
            "Icebreaker suggestions"
        ],
        "capabilities": [
            "Companion creation with customizable traits and conversation styles",
            "Photo upload with animated effects for ideal soulmate representation",
            "Persistent memory system for personal details and stories",
            "Daily care, compliments, and mood check-ins",
            "11-question matchmaking questionnaire (Simple + Deep Learning)",
            "1 free daily human match with additional purchases via AC/AB",
            "Compatibility percentage and detailed match reports",
            "Secure chat with mutual consent system",
            "Integration with Level 1 AnamProfile verification",
            "Modular algorithm reusable for SoulVibe feature"
        ],
        "keywords": ["match", "dating", "relationship", "love", "companion", "soulmate",
                     "compatibility", "romance", "partner", "connection", "destiny",
                     "ai companion", "matchmaking", "human match"]
    },
    "lokaris": {
        "name": "LOKARIS (Games & Entertainment)",
        "description": "AR games, multiplayer experiences, and community-driven gaming.",
        "features": [
            "AR-based interactive reality games",
            "Multiplayer Chess with real-time PvP and Player vs AI",
            "Arcade microgames (trivia, puzzle, reaction-based)",
            "Team chess modes (2v2 up to 5v5)",
            "Leaderboards and tournament systems",
            "Game creator studio for user-generated content"
        ],
        "available_games": [
            {
                "name": "Om Nom Run",
                "developer": "Famobi",
                "category": "Endless Runner",
                "description": "Join Om Nom on an exciting endless running adventure! Dodge obstacles, collect candies, and unlock power-ups in this fast-paced runner game."
            },
            {
                "name": "Moto X3M Pool Party",
                "developer": "Famobi",
                "category": "Racing & Sports",
                "description": "Rev up your engines for the ultimate summer racing adventure! Perform crazy stunts and tricks while racing through water parks and pool-themed tracks."
            },
            {
                "name": "Thug Racer",
                "developer": "Famobi",
                "category": "Racing & Action",
                "description": "Take control of powerful cars and dominate the streets in this intense urban racing game. Customize your vehicle, perform daring drifts, and outrun your opponents in thrilling city races."
            }
        ],
        "capabilities": [
            "Real-time multiplayer gaming with low latency",
            "AR game overlays with WebXR integration",
            "Chess tournaments with live streaming",
            "Waging system with AnamCoins and AccessBonus",
            "SoulPoints and rewards for gameplay",
            "Cross-platform gaming (mobile-first, PWA-ready)",
            "Anti-cheat and content moderation systems",
            "Integration with SoulStream for live play",
            "Achievement sharing to SoulFeed",
            "Daily quests and stat tracking"
        ],
        "keywords": ["game", "chess", "play", "arcade", "ar", "multiplayer", "pvp",
                     "tournament", "competition", "gaming", "entertainment", "fun",
                     "battle", "arena", "lokaris", "racing", "runner", "om nom",
                     "moto", "thug racer", "stunts", "drifts", "endless runner"]
    }
}


# ============================================================
# SUPABASE DATABASE HANDLER
# ============================================================
class SupabaseHandler:
    def __init__(self):
        self.table_name = "chat_conversations_anamguru"

    async def get_conversation_history(self, user_id: str, module: str) -> List[Dict]:
        try:
            response = supabase.table(self.table_name).select("*").eq(
                "user_id", user_id
            ).eq("module", module).execute()

            if response.data and len(response.data) > 0:
                return response.data[0].get("chat_conversations_anamguru", [])
            return []

        except Exception as e:
            print(f"[Memory] Error retrieving history: {str(e)}")
            return []

    async def save_conversation(
        self,
        user_id: str,
        module: str,
        new_message: Dict,
        bot_response: str
    ) -> bool:
        try:
            existing = supabase.table(self.table_name).select("*").eq(
                "user_id", user_id
            ).eq("module", module).execute()

            user_msg = {
                "role": "user",
                "content": new_message.get("content", ""),
                "timestamp": datetime.utcnow().isoformat()
            }
            bot_msg = {
                "role": "assistant",
                "content": bot_response,
                "timestamp": datetime.utcnow().isoformat()
            }

            if existing.data and len(existing.data) > 0:
                history = existing.data[0].get("chat_conversations_anamguru", [])
                history.append(user_msg)
                history.append(bot_msg)
                # Keep last 50 messages only
                if len(history) > 50:
                    history = history[-50:]

                supabase.table(self.table_name).update({
                    "chat_conversations_anamguru": history,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("user_id", user_id).eq("module", module).execute()
            else:
                supabase.table(self.table_name).insert({
                    "user_id": user_id,
                    "module": module,
                    "chat_conversations_anamguru": [user_msg, bot_msg],
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }).execute()

            return True

        except Exception as e:
            print(f"[Memory] Error saving conversation: {str(e)}")
            return False

    async def get_all_user_conversations(self, user_id: str) -> List[Dict]:
        try:
            response = supabase.table(self.table_name).select("*").eq(
                "user_id", user_id
            ).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"[Memory] Error retrieving all conversations: {str(e)}")
            return []

    async def delete_conversation(self, user_id: str, module: str) -> bool:
        try:
            supabase.table(self.table_name).delete().eq(
                "user_id", user_id
            ).eq("module", module).execute()
            return True
        except Exception as e:
            print(f"[Memory] Error deleting conversation: {str(e)}")
            return False


# ============================================================
# ANAMCORE CHATBOT ENGINE
# ============================================================
class AnamcaraChatbot:
    def __init__(self):
        # self.api_url = "https://api.openai.com/v1/chat/completions"
        # self.model = "gpt-4o"
        # self.api_key = OPENAI_API_KEY
        self.db = SupabaseHandler()

    def detect_module(self, query: str) -> Tuple[str, float]:
        """Detect which Guru module the query relates to."""
        query_lower = query.lower()
        scores = {}

        for module_id, module_data in MODULE_KNOWLEDGE.items():
            score = 0
            for keyword in module_data["keywords"]:
                if keyword in query_lower:
                    score += 1

            # Strong boost if Guru name mentioned directly
            if module_id in query_lower or module_data["name"].split("(")[0].strip().lower() in query_lower:
                score += 5

            scores[module_id] = score

        best_module = max(scores.items(), key=lambda x: x[1])

        if best_module[1] == 0:
            return "general", 0.0

        total = sum(scores.values())
        confidence = round(best_module[1] / total, 2) if total > 0 else 0.0
        return best_module[0], confidence

    def build_system_prompt(self, module: str, query: str) -> str:
        """Build full system prompt = Personality Layer + Knowledge Layer."""

        # ---- General fallback (no specific module) ----
        if module == "general":
            context = "You are the ANAMCORE central guide for the Anamcara AI ecosystem.\n\n"
            context += "Available Guru modules:\n\n"
            for mod_id, mod_data in MODULE_KNOWLEDGE.items():
                context += f"{mod_data['name']}: {mod_data['description']}\n"
            context += "\nHelp the user find the right Guru module for their needs."
            return context

        # ---- Module-specific prompt ----
        module_data = MODULE_KNOWLEDGE.get(module, {})
        personality = GURU_PERSONALITIES.get(module, {})

        guru_character = personality.get("character", module_data["name"])
        guru_tone = personality.get("tone", "Helpful and professional")
        guru_redirect = personality.get(
            "redirect",
            "That question belongs to another Guru module."
        )

        prompt = f"""You are {guru_character}.

PERSONALITY AND TONE:
{guru_tone}

YOUR DOMAIN — {module_data['name']}:
{module_data['description']}

AVAILABLE FEATURES:
{chr(10).join(f"- {f}" for f in module_data['features'])}

CAPABILITIES:
{chr(10).join(f"- {c}" for c in module_data['capabilities'])}"""

        # Extra context for specific modules
        if module == "lokaris" and "available_games" in module_data:
            prompt += "\n\nAVAILABLE GAMES:\n"
            for game in module_data["available_games"]:
                prompt += f"\n- {game['name']} by {game['developer']} ({game['category']})\n"
                prompt += f"  {game['description']}\n"

        if module == "athena" and "available_tests" in module_data:
            prompt += "\n\nAVAILABLE TESTS:\n"
            for test in module_data["available_tests"]:
                prompt += f"- {test}\n"

        prompt += f"""

CRITICAL INSTRUCTIONS:

1. STAY IN CHARACTER as {guru_character.split(',')[0]} at all times. Never break character.

2. YOU ARE A GUIDE, NOT A SERVICE PROVIDER:
   - Do NOT ask users for personal information to provide actual services
   - EXPLAIN what features are available and how to access them
   - Use phrases like "This module offers...", "You can access...", "Available features include..."

3. OUT-OF-SCOPE QUESTIONS:
   - If the user asks something unrelated to your domain, respond:
     "{guru_redirect}"
   - Do not attempt to answer out-of-scope questions

4. FORMATTING RULES (STRICT):
   - Do NOT use asterisks (* or **)
   - Do NOT use markdown bold or italic
   - Do NOT use bullet points starting with *
   - Use plain text with line breaks for structure
   - Keep responses clean and readable

User Query: {query}"""

        return prompt

    async def generate_response(
        self,
        query: str,
        module: str,
        conversation_history: List[Dict]
    ) -> str:
        """Generate response using OpenAI GPT-4o."""
        system_prompt = self.build_system_prompt(module, query)

        messages = [{"role": "system", "content": system_prompt}]

        # Include last 10 messages from history for context
        for msg in conversation_history[-10:]:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })

        messages.append({"role": "user", "content": query})

        try:
            # messages list ko single prompt string mein convert karo
            prompt_parts = []
            for msg in messages:
                role = msg["role"].upper()
                content = msg["content"]
                prompt_parts.append(f"{role}: {content}")
            prompt_parts.append("ASSISTANT:")
            full_prompt = "\n\n".join(prompt_parts)

            # Phir tumhara existing Ollama call use karo
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    # "https://anamcara.ai/llama/api/generate",
                    "http://192.168.18.61:11434/api/generate",
                    json={
                        "model": "llama3.2",
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "num_predict": 1000,
                            "temperature": 0.7,
                        }
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("response", "").strip()
            return "Error: No response generated"

        except Exception as e:
            return f"Error generating response: {str(e)}"

    def get_related_features(self, module: str) -> List[str]:
        module_data = MODULE_KNOWLEDGE.get(module, {})
        return module_data.get("features", [])[:5]

    def get_suggestions(self, module: str) -> List[str]:
        suggestions_map = {
            "divine": ["Try a tarot card reading", "Get your daily horoscope",
                       "Calculate your Life Path Number", "Interpret a recent dream"],
            "athena": ["Take an IQ test (1 AC)", "Challenge someone in AnamClash",
                       "View leaderboards", "Try the EQ assessment"],
            "destiny": ["Create your AI companion", "Find your human match",
                        "Take the compatibility quiz", "Set up your matchmaking profile"],
            "lokaris": ["Play multiplayer chess", "Try Om Nom Run",
                        "Race in Moto X3M Pool Party", "Join a tournament"],
            "caishen": ["Take the financial literacy assessment", "Explore startup strategy quizzes",
                        "Try investment risk simulations"],
            "apollo": ["Take the fitness assessment", "Try nutrition science quizzes",
                       "Check the athlete leaderboard"],
            "vulcan": ["Try mechanical reasoning tests", "Take the automotive knowledge quiz",
                       "Join the engineering leaderboard"],
            "general": ["Explore DIVINE for spiritual guidance", "Try ATHENA for brain tests",
                        "Visit DESTINY for matchmaking", "Play games in LOKARIS"]
        }
        return suggestions_map.get(module, [])


# Initialize chatbot
chatbot = AnamcaraChatbot()


# ============================================================
# ORIGINAL PERSONA CHAT ENDPOINTS (unchanged)
# ============================================================
@router.post("/", response_model=ChatResponse)
async def chat(chat_message: ChatMessage):
    try:
        client = get_client()
        persona_result = client.table("personas").select("*").eq("id", chat_message.persona_id).execute()

        if not persona_result.data:
            raise HTTPException(status_code=404, detail="Persona not found")

        persona = persona_result.data[0]
        current_time = datetime.utcnow()

        chat_history_result = client.table("chat_messages").select("*").eq(
            "thread_id", chat_message.thread_id
        ).order("timestamp", desc=False).execute()

        messages = []
        if chat_history_result.data:
            for msg in chat_history_result.data:
                role = "user" if msg["sender"] == "user" else "assistant"
                messages.append({"role": role, "content": msg["message"]})

        messages.append({"role": "user", "content": chat_message.message})

        ai_response = await generate_chat_response(messages, persona)

        user_message_data = {
            "thread_id": chat_message.thread_id,
            "persona_id": chat_message.persona_id,
            "user_id": persona["user_id"],
            "sender": "user",
            "message": chat_message.message,
            "timestamp": current_time.isoformat()
        }
        ai_message_data = {
            "thread_id": chat_message.thread_id,
            "persona_id": chat_message.persona_id,
            "user_id": persona["user_id"],
            "sender": "ai",
            "message": ai_response,
            "timestamp": current_time.isoformat()
        }

        client.table("chat_messages").insert([user_message_data, ai_message_data]).execute()
        client.table("personas").update({
            "last_interaction": current_time.isoformat()
        }).eq("id", chat_message.persona_id).execute()

        return ChatResponse(
            response=ai_response,
            thread_id=chat_message.thread_id,
            persona_id=chat_message.persona_id,
            timestamp=current_time
        )

    except Exception as e:
        error_message = str(e)
        if "invalid_api_key" in error_message or "Incorrect API key" in error_message:
            raise HTTPException(status_code=401, detail="Service configuration error. Please contact the administrator.")
        elif "429" in error_message or "rate limit" in error_message.lower():
            raise HTTPException(status_code=429, detail="Service is currently overloaded. Please try again in a few moments.")
        print(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")


@router.get("/history/{thread_id}")
async def get_chat_history(thread_id: str, limit: int = 50):
    try:
        client = get_client()
        result = client.table("chat_messages").select("*").eq(
            "thread_id", thread_id
        ).order("timestamp", desc=False).limit(limit).execute()

        if not result.data:
            return {"messages": []}
        return {"messages": [serialize_doc(msg) for msg in result.data]}

    except Exception as e:
        print(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get chat history: {str(e)}")


@router.get("/threads/{user_id}")
async def get_user_chat_threads(user_id: str):
    try:
        client = get_client()
        result = client.table("chat_messages").select("""
            thread_id,
            persona_id,
            personas!inner(name, gender),
            message,
            timestamp
        """).eq("user_id", user_id).order("timestamp", desc=True).execute()

        threads = {}
        for msg in result.data:
            thread_id = msg["thread_id"]
            if thread_id not in threads:
                threads[thread_id] = {
                    "thread_id": thread_id,
                    "persona_id": msg["persona_id"],
                    "persona_name": msg["personas"]["name"],
                    "persona_gender": msg["personas"]["gender"],
                    "last_message": msg["message"],
                    "last_timestamp": msg["timestamp"]
                }
        return {"threads": list(threads.values())}

    except Exception as e:
        print(f"Error getting chat threads: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get chat threads: {str(e)}")


@router.delete("/thread/{thread_id}")
async def delete_chat_thread(thread_id: str):
    try:
        client = get_client()
        client.table("chat_messages").delete().eq("thread_id", thread_id).execute()
        return {"message": "Chat thread deleted successfully"}
    except Exception as e:
        print(f"Error deleting chat thread: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete chat thread: {str(e)}")


# ============================================================
# ANAMGURU CHAT ENDPOINTS
# ============================================================
@router.post("/anamguru_chat", response_model=ChatResponseModules)
async def anamguru_chat(request: ChatRequest):
    """Main AnamGuru chat endpoint with personality layer + RAG routing + Supabase memory."""

    if not request.user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    # Determine module
    if request.module:
        module_lower = request.module.lower()
        if module_lower not in MODULE_KNOWLEDGE and module_lower != "general":
            raise HTTPException(
                status_code=400,
                detail=f"Invalid module. Available: {', '.join(MODULE_KNOWLEDGE.keys())}"
            )
        detected_module = module_lower
        confidence = 1.0
    else:
        detected_module, confidence = chatbot.detect_module(request.query)

    # Load conversation history from Supabase
    conversation_history = await chatbot.db.get_conversation_history(
        request.user_id,
        detected_module
    )

    # Generate response with personality + knowledge
    response_text = await chatbot.generate_response(
        query=request.query,
        module=detected_module,
        conversation_history=conversation_history
    )

    # Save to Supabase
    await chatbot.db.save_conversation(
        user_id=request.user_id,
        module=detected_module,
        new_message={"content": request.query},
        bot_response=response_text
    )

    related_features = chatbot.get_related_features(detected_module)
    suggestions = chatbot.get_suggestions(detected_module)
    conversation_id = f"{request.user_id}_{detected_module}"

    return ChatResponseModules(
        response=response_text,
        detected_module=detected_module,
        confidence=confidence,
        related_features=related_features,
        suggestions=suggestions,
        conversation_id=conversation_id
    )


@router.get("/anam_guru_conversations/{user_id}")
async def get_user_conversations(user_id: str):
    conversations = await chatbot.db.get_all_user_conversations(user_id)
    return {
        "user_id": user_id,
        "total_conversations": len(conversations),
        "conversations": conversations
    }


@router.get("/anam_guru_conversations/{user_id}/{module}")
async def get_conversation_by_module(user_id: str, module: str):
    if module not in MODULE_KNOWLEDGE and module != "general":
        raise HTTPException(status_code=404, detail="Module not found")

    history = await chatbot.db.get_conversation_history(user_id, module)
    return {
        "user_id": user_id,
        "module": module,
        "conversation_history": history,
        "total_messages": len(history)
    }


@router.delete("/anam_guru_conversations/{user_id}/{module}")
async def delete_conversation(user_id: str, module: str):
    if module not in MODULE_KNOWLEDGE and module != "general":
        raise HTTPException(status_code=404, detail="Module not found")

    success = await chatbot.db.delete_conversation(user_id, module)
    if success:
        return {"message": "Conversation deleted successfully", "user_id": user_id, "module": module}
    raise HTTPException(status_code=500, detail="Failed to delete conversation")
