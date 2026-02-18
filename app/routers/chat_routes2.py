# # REal chat rote we using with 4 gurus
# # routes/chat_routes.py
# from fastapi import APIRouter, HTTPException
# from models.schemas import ChatMessage, ChatResponse, ChatResponseModules, ChatRequest
# from app.services.openai_service import generate_chat_response
# from models.supabase_helpers import serialize_doc
# from database.supabase_db import get_client
# from datetime import datetime
# from typing import Optional, Dict, List
# import httpx
# import json
# from enum import Enum
# import os

# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# router = APIRouter()
# supabase = get_client()


# # Module Knowledge Base
# MODULE_KNOWLEDGE = {
#     "divine": {
#         "name": "DIVINE (Divination AnamGuru)",
#         "description": "Ethereal AI entity for spiritual guidance, wisdom, and introspection",
#         "features": [
#             "Tarot Card Readings with dream symbolism integration",
#             "Daily Horoscopes based on zodiac signs with personalized insights",
#             "Numerology Analysis including Life Path Number calculations",
#             "Dream Interpretation to uncover hidden meanings",
#             "Astrological Reflections with birth chart analysis",
#             "Interactive Tarot Chat for guidance on specific situations"
#         ],
#         "capabilities": [
#             "Personalized tarot spreads (Single Card, Three Card, Relationship)",
#             "Virtual card draw simulation with contextual interpretations",
#             "Dream-to-Tarot linkage for deeper insights",
#             "Zodiac sign determination and daily horoscope delivery",
#             "Lucky numbers, colors, and compatibility readings",
#             "Life Path Number calculation using numerological reduction",
#             "Comprehensive personality trait analysis through numbers"
#         ],
#         "keywords": ["tarot", "horoscope", "astrology", "numerology", "dream", "divination", 
#                      "zodiac", "spiritual", "guidance", "cards", "fortune", "prediction",
#                      "birth chart", "life path", "mystical"]
#     },
#     "vulcan": {
#         "name": "VULCAN (Automotive & Engineering AnamGuru)",
#         "description": "A technical intelligence module focused on innovation, engineering logic, mechanical mastery, and industrial creativity. VULCAN develops analytical thinking, system design ability, and problem-solving skills across automotive, robotics, and modern engineering domains.",
#         "features": [
#             "Mechanical reasoning assessments",
#             "Automotive technology knowledge tests",
#             "Engineering design-thinking challenges",
#             "Problem-solving and system logic quizzes",
#             "Innovation and product development simulations",
#             "Electric vehicle and smart mobility assessments",
#             "Robotics and automation intelligence tests"
#             ],
#     "capabilities": [
#         "Engineering skill ranking leaderboard",
#         "Technical innovation battle mode",
#         "Industry-focused certification badges",
#         "Performance optimization challenges",
#         "Real-time engineering quiz arena",
#         "Analytical intelligence scoring reports",
#         "Gamified industrial design competitions"
#     ],
#     "keywords": [
#         "automotive", "engineering", "mechanical",
#         "innovation", "robotics", "industrial",
#         "design", "machine", "technology",
#         "automation", "vehicles"
#     ]
#     },
#     "venus": {
#     "name": "VENUS (Fashion & Beauty AnamGuru)",
#     "description": "A style and identity intelligence module focused on aesthetic awareness, personal branding, fashion psychology, and beauty evolution. VENUS enhances creativity, visual taste, self-expression, and cultural style intelligence for modern fashion and lifestyle domains.",
#     "features": [
#         "Style personality assessments",
#         "Fashion trend intelligence quizzes",
#         "Beauty psychology and identity analysis",
#         "Color theory and aesthetic harmony tests",
#         "Personal branding evaluation",
#         "Luxury and lifestyle knowledge challenges",
#         "Creative styling scenario simulations"
#     ],
#     "capabilities": [
#         "Style influence leaderboard",
#         "Personal aesthetic scoring system",
#         "Brand identity development insights",
#         "Trend forecasting challenges",
#         "Virtual styling battle mode",
#         "Fashion intelligence certificates",
#         "Creative portfolio growth tracking"
#     ],
#     "keywords": [
#         "fashion", "beauty", "style",
#         "aesthetic", "luxury", "branding",
#         "makeup", "trend", "identity",
#         "model", "creative"
#     ]
#     },
#     "monroe": {
#     "name": "MONROE (Media & Entertainment AnamGuru)",
#     "description": "A dynamic creative intelligence module focused on developing confidence, storytelling ability, public presence, and audience influence. MONROE is designed to enhance performance psychology, digital charisma, and entertainment-driven skills for modern creators and media personalities.",
#     "features": [
#         "Public speaking and stage confidence assessment",
#         "Creative personality archetype analysis",
#         "Viral potential and influence scoring",
#         "Performance psychology evaluation",
#         "Storytelling and scriptwriting challenges",
#         "Content strategy intelligence quizzes",
#         "On-camera presence evaluation"
#     ],
#     "capabilities": [
#         "Creator ranking and visibility leaderboard",
#         "Audience engagement scoring system",
#         "Brand persona and identity analysis",
#         "Live performance battle mode",
#         "Content growth and positioning insights",
#         "Creativity strength mapping with detailed reports",
#         "Gamified media challenges across film, music, and digital platforms"
#     ],
#     "keywords": [
#         "media", "entertainment", "creator",
#         "performance", "acting", "film",
#         "music", "influencer", "viral",
#         "content", "brand", "creative"
#     ]
#     },
#     "mary": {
#     "name": "MARY (Parenting & Caregiving AnamGuru)",
#     "description": "A nurturing intelligence module focused on emotional care, child development, family psychology, and compassionate leadership within households and caregiving environments. MARY enhances patience, emotional intelligence, guidance skills, and supportive decision-making.",
#     "features": [
#         "Parenting style assessment",
#         "Child development knowledge tests",
#         "Emotional intelligence for caregivers",
#         "Family communication challenges",
#         "Behavioral guidance simulations",
#         "Conflict resolution in family dynamics",
#         "Healthy attachment style evaluation"
#     ],
#     "capabilities": [
#         "Caregiver strength scoring reports",
#         "Family leadership growth tracking",
#         "Emotional support intelligence analysis",
#         "Scenario-based parenting challenges",
#         "Child psychology insight modules",
#         "Relationship harmony improvement tools",
#         "Gamified caregiving knowledge arena"
#     ],
#     "keywords": [
#         "parenting", "caregiver", "family",
#         "child", "mother", "father",
#         "guidance", "nurturing", "support",
#         "development", "home"
#     ]
# },
# "lilith": {
#     "name": "LILITH (Rebellion, Hacking & Conspiracies AnamGuru)",
#     "description": "A critical-thinking and unconventional intelligence module designed to explore cybersecurity, ethical hacking, underground culture, truth analysis, and alternative narratives. LILITH sharpens investigative reasoning, digital defense skills, and bold independent thinking.",
#     "features": [
#         "Cybersecurity fundamentals assessment",
#         "Ethical hacking knowledge tests",
#         "Critical thinking and deception detection quizzes",
#         "Conspiracy theory analysis challenges",
#         "Digital privacy awareness evaluation",
#         "Social engineering scenario simulations",
#         "Underground culture intelligence tests"
#     ],
#     "capabilities": [
#         "Cyber skill ranking leaderboard",
#         "Security awareness scoring reports",
#         "Logic vs misinformation battle mode",
#         "Digital defense certification badges",
#         "Ethical hacking challenge arena",
#         "Critical reasoning strength analysis",
#         "Advanced investigative simulations"
#     ],
#     "keywords": [
#         "hacking", "cyber", "security",
#         "rebellion", "truth", "conspiracy",
#         "privacy", "investigation",
#         "dark web", "analysis"
#     ]
# },
# "joseph": {
#     "name": "JOSEPH (Real Estate & Construction AnamGuru)",
#     "description": "A strategic development module focused on property intelligence, architecture fundamentals, construction planning, and investment growth. JOSEPH builds practical knowledge in real estate markets, structural design, and long-term asset creation.",
#     "features": [
#         "Real estate investment knowledge tests",
#         "Construction fundamentals assessment",
#         "Architecture and spatial planning quizzes",
#         "Property valuation simulations",
#         "Urban development intelligence challenges",
#         "Home design logic tests",
#         "Market trend analysis exercises"
#     ],
#     "capabilities": [
#         "Property strategy scoring reports",
#         "Investment risk analysis tools",
#         "Construction planning simulations",
#         "Developer ranking leaderboard",
#         "Real estate negotiation challenges",
#         "Portfolio growth tracking system",
#         "Infrastructure knowledge certifications"
#     ],
#     "keywords": [
#         "real estate", "construction", "property",
#         "investment", "architecture", "housing",
#         "development", "builder", "market",
#         "infrastructure"
#     ]
# },
# "hikari": {
#     "name": "HIKARI (Legal, Policy & Government AnamGuru)",
#     "description": "A civic intelligence module centered on law, governance, public policy, rights awareness, and ethical leadership. HIKARI develops analytical reasoning, justice-based thinking, and structured debate skills for societal impact.",
#     "features": [
#         "Legal reasoning assessments",
#         "Public policy knowledge quizzes",
#         "Constitution and rights awareness tests",
#         "Debate and argumentation challenges",
#         "Civic literacy evaluation",
#         "Ethical leadership simulations",
#         "Government systems intelligence tests"
#     ],
#     "capabilities": [
#         "Policy analysis scoring system",
#         "Legal knowledge leaderboard",
#         "Debate battle arena",
#         "Civic awareness certifications",
#         "Public speaking for advocacy challenges",
#         "Critical reasoning strength reports",
#         "Governance strategy simulations"
#     ],
#     "keywords": [
#         "law", "policy", "government",
#         "justice", "legal", "rights",
#         "debate", "constitution",
#         "civic", "leadership"
#     ]
# },
# "ceres": {
#     "name": "CERES (Agriculture & Environment AnamGuru)",
#     "description": "A sustainability intelligence module focused on agriculture, environmental awareness, ecological balance, and green innovation. CERES develops knowledge in farming systems, climate responsibility, food security, and regenerative environmental practices.",
#     "features": [
#         "Sustainable farming knowledge assessments",
#         "Climate change awareness quizzes",
#         "Environmental protection challenges",
#         "Food security intelligence tests",
#         "Eco-innovation simulations",
#         "Soil and crop management evaluations",
#         "Renewable resource knowledge exercises"
#     ],
#     "capabilities": [
#         "Sustainability impact scoring system",
#         "Green innovation leaderboard",
#         "Environmental strategy simulations",
#         "Agriculture knowledge certifications",
#         "Eco-awareness challenge arena",
#         "Climate literacy progress tracking",
#         "Community sustainability ranking"
#     ],
#     "keywords": [
#         "agriculture", "environment", "climate",
#         "sustainability", "farming", "eco",
#         "green", "food", "conservation",
#         "nature"
#     ]
# },
# "cameron": {
#     "name": "CAMERON (Technology & Innovation AnamGuru)",
#     "description": "A future-focused intelligence module centered on emerging technologies, startup ecosystems, product innovation, and digital transformation. CAMERON enhances technical thinking, entrepreneurial mindset, and breakthrough problem-solving skills.",
#     "features": [
#         "Emerging technology knowledge tests",
#         "Startup and product strategy assessments",
#         "AI and software fundamentals quizzes",
#         "Innovation mindset evaluation",
#         "Tech trend analysis challenges",
#         "Digital transformation simulations",
#         "Future scenario problem-solving exercises"
#     ],
#     "capabilities": [
#         "Innovation ranking leaderboard",
#         "Startup strategy scoring system",
#         "Tech battle arena mode",
#         "Product development simulations",
#         "Digital skills certification badges",
#         "Future-readiness intelligence reports",
#         "Entrepreneurial growth tracking"
#     ],
#     "keywords": [
#         "technology", "innovation", "startup",
#         "ai", "software", "digital",
#         "product", "future", "tech",
#         "entrepreneur"
#     ]
# },
# "desire": {
#     "name": "DESIRE (Romance, Travel & Lifestyle AnamGuru)",
#     "description": "A freedom-driven lifestyle intelligence module focused on romantic exploration, travel psychology, pleasure-based living, and experiential growth. DESIRE enhances spontaneity, cultural awareness, relationship energy, and life-enjoyment intelligence for modern explorers and romantics.",
#     "features": [
#         "Romantic personality assessments",
#         "Travel compatibility and adventure quizzes",
#         "Lifestyle freedom evaluation",
#         "Cultural intelligence challenges",
#         "Relationship chemistry analysis",
#         "Experience-based decision-making tests",
#         "Bucket-list and life exploration tracking"
#     ],
#     "capabilities": [
#         "Romance and attraction scoring system",
#         "Travel intelligence leaderboard",
#         "Lifestyle alignment analysis reports",
#         "Adventure challenge arena",
#         "Couple compatibility insights",
#         "Freedom and fulfillment tracking",
#         "Experiential growth mapping"
#     ],
#     "keywords": [
#         "romance", "travel", "lifestyle",
#         "adventure", "love", "freedom",
#         "exploration", "nomad",
#         "culture", "experience"
#     ]
# },
# "callisto": {
#     "name": "CALLISTO (LGBTQIA+ Empowerment & Identity AnamGuru)",
#     "description": "An identity and empowerment intelligence module focused on self-expression, inclusion awareness, gender diversity understanding, and community strength. CALLISTO promotes confidence, advocacy knowledge, and social equality literacy.",
#     "features": [
#         "Identity exploration assessments",
#         "Gender and diversity knowledge quizzes",
#         "Inclusion and allyship evaluation",
#         "Confidence and self-expression tests",
#         "Community history and rights awareness challenges",
#         "Advocacy communication simulations",
#         "Personal empowerment tracking exercises"
#     ],
#     "capabilities": [
#         "Empowerment growth scoring reports",
#         "Inclusion awareness leaderboard",
#         "Advocacy debate arena",
#         "Community engagement certifications",
#         "Confidence development tracking",
#         "Equality literacy assessments",
#         "Safe-space dialogue simulations"
#     ],
#     "keywords": [
#         "identity", "diversity", "inclusion",
#         "empowerment", "gender", "equality",
#         "community", "rights", "expression",
#         "advocacy"
#     ]
# },
# "caishen": {
#     "name": "CAISHEN (Business, Wealth & Startups AnamGuru)",
#     "description": "A financial intelligence module focused on entrepreneurship, investment strategy, wealth-building psychology, and business leadership. CAISHEN strengthens decision-making, financial literacy, and scalable growth thinking.",
#     "features": [
#         "Financial literacy assessments",
#         "Entrepreneurship knowledge tests",
#         "Investment strategy quizzes",
#         "Startup growth simulations",
#         "Business negotiation challenges",
#         "Wealth mindset evaluation",
#         "Market analysis exercises"
#     ],
#     "capabilities": [
#         "Wealth intelligence scoring system",
#         "Entrepreneur leaderboard rankings",
#         "Investment risk simulation arena",
#         "Business strategy certifications",
#         "Startup performance tracking",
#         "Portfolio growth analytics",
#         "Financial decision-making reports"
#     ],

#     "keywords": [
#         "business", "wealth", "startup",
#         "investment", "finance", "entrepreneur",
#         "money", "market", "strategy",
#         "growth"
#     ]
# },
# "apollo": {
#     "name": "APOLLO (Health, Sports, Fitness & Nutrition AnamGuru)",
#     "description": "A vitality intelligence module focused on physical performance, nutrition science, athletic mindset, and holistic health optimization. APOLLO enhances discipline, endurance, and wellness awareness.",
#     "features": [
#         "Fitness knowledge assessments",
#         "Nutrition science quizzes",
#         "Athletic performance evaluation",
#         "Workout strategy simulations",
#         "Mental resilience and discipline tests",
#         "Sports intelligence challenges",
#         "Healthy lifestyle habit tracking"
#     ],
#     "capabilities": [
#         "Performance scoring system",
#         "Athlete ranking leaderboard",
#         "Training plan simulation arena",
#         "Nutrition intelligence certifications",
#         "Wellness progress tracking",
#         "Recovery and resilience analysis",
#         "Personal fitness growth reports"
#     ],
#     "keywords": [
#         "fitness", "health", "nutrition",
#         "sports", "training", "wellness",
#         "strength", "discipline",
#         "performance", "athlete"
#     ]
# },
# "anubis": {
#     "name": "ANUBIS (Afterlife, Soul Sanctuary & Ancestors AnamGuru)",
#     "description": "A reflective intelligence module centered on grief processing, ancestral understanding, legacy awareness, and life-after-death philosophy. ANUBIS supports emotional healing, remembrance, and spiritual contemplation.",
#     "features": [
#         "Grief reflection assessments",
#         "Ancestral heritage exploration quizzes",
#         "Legacy and life-impact evaluation",
#         "Afterlife philosophy challenges",
#         "Memorialization planning simulations",
#         "Spiritual transition awareness exercises",
#         "Emotional healing journaling prompts"
#     ],
#     "capabilities": [
#         "Healing progress tracking reports",
#         "Legacy reflection scoring system",
#         "Philosophical discussion arena",
#         "Ancestral connection insights",
#         "Emotional resilience analysis",
#         "Memorial planning guidance tools",
#         "Spiritual contemplation certifications"
#     ],
#     "keywords": [
#         "afterlife", "ancestors", "grief",
#         "legacy", "spiritual", "healing",
#         "soul", "reflection",
#         "memorial", "philosophy"
#     ]
# },
# "amaterasu": {
#     "name": "AMATERASU (Mental Health, Yoga & Meditation AnamGuru)",
#     "description": "A holistic well-being intelligence module focused on mental clarity, emotional healing, mindfulness, yoga philosophy, and inner balance. AMATERASU supports burnout recovery, stress regulation, self-awareness development, and sustainable personal renewal.",
#     "features": [
#         "Mental wellness self-assessments",
#         "Stress and burnout evaluation tests",
#         "Mindfulness and meditation knowledge quizzes",
#         "Yoga philosophy and practice intelligence checks",
#         "Emotional regulation exercises",
#         "Breathing technique simulations",
#         "Self-reflection and awareness tracking"
#     ],
#     "capabilities": [
#         "Mental resilience scoring system",
#         "Burnout recovery progress tracking",
#         "Guided mindfulness challenge arena",
#         "Emotional balance analytics reports",
#         "Meditation streak and habit builder",
#         "Holistic wellness certifications",
#         "Personal growth and clarity mapping"
#     ],
#     "keywords": [
#         "mental health", "meditation", "yoga",
#         "mindfulness", "healing", "burnout",
#         "stress", "wellness",
#         "emotional balance", "self-care"
#     ]
# },
# "gabriel": {
#     "name": "GABRIEL (Religion & Spiritual Guidance AnamGuru)",
#     "description": "A spiritual intelligence module focused on faith exploration, moral reasoning, inner growth, and philosophical understanding. GABRIEL enhances reflection, purpose discovery, and values-based decision-making across spiritual traditions.",
#     "features": [
#         "Spiritual awareness assessments",
#         "Moral reasoning and ethics quizzes",
#         "Philosophical thought challenges",
#         "Comparative religion knowledge tests",
#         "Purpose and life-direction evaluation",
#         "Meditation and mindfulness simulations",
#         "Scriptural literacy exercises"
#     ],
#     "capabilities": [
#         "Spiritual growth tracking reports",
#         "Values alignment scoring system",
#         "Ethical dilemma challenge arena",
#         "Faith-based knowledge certifications",
#         "Reflection and journaling insights",
#         "Inner development progress mapping",
#         "Philosophy discussion battles"
#     ],
#     "keywords": [
#         "religion", "spiritual", "faith",
#         "ethics", "philosophy", "guidance",
#         "purpose", "morality",
#         "belief", "reflection"
#     ]
# },
#     "athena": {
#         "name": "ATHENA (Intelligence, Mind & Challenge AnamGuru)",
#         "description": "Education and career development through brain tests and gamified knowledge battles",
#         "features": [
#             "AnamTests: 11 premium intelligence and personality tests",
#             "AnamClash: Real-time 1v1 quiz battles",
#             "SoulArena: Team-based quiz competitions (2v2 to 5v5)",
#             "IQ, EQ, and personality assessments with certificates",
#             "Cognitive and behavioral psychology tests",
#             "Academic skill tests (English, Math, Science)",
#             "Tech & Digital Literacy assessments"
#         ],
#         "capabilities": [
#             "Paid intelligence tests (1 AnamCoin per test)",
#             "Test results with badges and AnamCertificates",
#             "Public/private result visibility options",
#             "Filterable leaderboards by test type and score",
#             "Real-time quiz battles with customizable settings",
#             "Multiple game modes: Single Player vs ANAMCORE, 1v1, Team battles",
#             "Category-based challenges (Science, Math, History, Tech, Pop Culture)",
#             "Betting system with AnamCoins and AccessBonus",
#             "Tiebreak logic and rematch options"
#         ],
#         "available_tests": [
#             "IQ Test", "EQ Test", "Big Five Personality", 
#             "Cognitive & Behavioral Psychology", "English Skills Quiz",
#             "Math Logic Challenge", "Science IQ Test", 
#             "Tech & Digital Literacy", "General Knowledge",
#             "Soul Age Quiz", "Introvert-Extrovert Meter"
#         ],
#         "keywords": ["test", "iq", "eq", "intelligence", "quiz", "battle", "clash", 
#                      "education", "learning", "challenge", "competition", "brain",
#                      "personality", "cognitive", "knowledge", "arena", "exam"]
#     },
    
#     "destiny": {
#         "name": "DESTINY (Matchmaking & Relationship AnamGuru)",
#         "description": "Matchmaking for meaningful emotional connections",
#         "features": [
#             "Destiny: Personalized ANAMCORE companion (ANAMCORE SoulMate)",
#             "Human Destiny: Matchmaking between real people",
#             "B2B Matchmaker API for external platform integration",
#             "Personality-adaptive ANAMCORE companions",
#             "Compatibility scoring with detailed reports",
#             "Icebreaker suggestions"
#         ],
#         "capabilities": [
#             "Companion creation with customizable traits and conversation styles",
#             "Photo upload with animated effects for ideal soulmate representation",
#             "Persistent memory system for personal details and stories",
#             "Daily care, compliments, and mood check-ins",
#             "11-question matchmaking questionnaire (Simple + Deep Learning)",
#             "1 free daily human match with additional purchases via AC/AB",
#             "Compatibility percentage and detailed match reports",
#             "Secure chat with mutual consent system",
#             "Integration with Level 1 AnamProfile verification",
#             "Modular algorithm reusable for SoulVibe feature"
#         ],
#         "keywords": ["match", "dating", "relationship", "love", "companion", "soulmate",
#                      "compatibility", "romance", "partner", "connection", "destiny",
#                      "ai companion", "matchmaking", "human match"]
#     },
    
#     "lokaris": {
#         "name": "LOKARIS (Games & Entertainment)",
#         "description": "AR games, multiplayer experiences, and community-driven gaming",
#         "features": [
#             "AR-based interactive reality games",
#             "Multiplayer Chess with real-time PvP and Player vs AI",
#             "Arcade microgames (trivia, puzzle, reaction-based)",
#             "Team chess modes (2v2 up to 5v5)",
#             "Leaderboards and tournament systems",
#             "Game creator studio for user-generated content"
#         ],
#         "available_games": [
#             {
#                 "name": "Om Nom Run",
#                 "developer": "Famobi",
#                 "category": "Endless Runner",
#                 "description": "Join Om Nom on an exciting endless running adventure! Dodge obstacles, collect candies, and unlock power-ups in this fast-paced runner game."
#             },
#             {
#                 "name": "Moto X3M Pool Party",
#                 "developer": "Famobi",
#                 "category": "Racing & Sports",
#                 "description": "Rev up your engines for the ultimate summer racing adventure! Perform crazy stunts and tricks while racing through water parks and pool-themed tracks."
#             },
#             {
#                 "name": "Thug Racer",
#                 "developer": "Famobi",
#                 "category": "Racing & Action",
#                 "description": "Take control of powerful cars and dominate the streets in this intense urban racing game. Customize your vehicle, perform daring drifts, and outrun your opponents in thrilling city races."
#             }
#         ],
#         "capabilities": [
#             "Real-time multiplayer gaming with low latency",
#             "AR game overlays with WebXR integration",
#             "Chess tournaments with live streaming",
#             "Waging system with AnamCoins and AccessBonus",
#             "SoulPoints and rewards for gameplay",
#             "Cross-platform gaming (mobile-first, PWA-ready)",
#             "Anti-cheat and content moderation systems",
#             "Integration with SoulStream for live play",
#             "Achievement sharing to SoulFeed",
#             "Daily quests and stat tracking",
#             "Endless runner games with power-ups and collectibles",
#             "Racing games with stunt mechanics and customization",
#             "Urban racing with vehicle customization and drifting"
#         ],
#         "keywords": ["game", "chess", "play", "arcade", "ar", "multiplayer", "pvp",
#                      "tournament", "competition", "gaming", "entertainment", "fun",
#                      "battle", "arena", "lokaris", "racing", "runner", "om nom",
#                      "moto", "thug racer", "stunts", "drifts", "endless runner"]
#     }
# }

# @router.post("/", response_model=ChatResponse)
# async def chat(chat_message: ChatMessage):
#     try:
#         client = get_client()
        
#         # Get persona details
#         persona_result = client.table("personas").select("*").eq("id", chat_message.persona_id).execute()
        
#         if not persona_result.data:
#             raise HTTPException(status_code=404, detail="Persona not found")
        
#         persona = persona_result.data[0]
#         current_time = datetime.utcnow()
        
#         # Get existing chat history for this thread
#         chat_history_result = client.table("chat_messages").select("*").eq("thread_id", chat_message.thread_id).order("timestamp", desc=False).execute()
        
#         # Prepare chat history for AI
#         messages = []
#         if chat_history_result.data:
#             for msg in chat_history_result.data:
#                 role = "user" if msg["sender"] == "user" else "assistant"
#                 messages.append({"role": role, "content": msg["message"]})
        
#         # Add current user message (not saved yet)
#         messages.append({"role": "user", "content": chat_message.message})
        
#         # Try to generate AI response
#         ai_response = await generate_chat_response(messages, persona)
        
#         user_message_data = {
#             "thread_id": chat_message.thread_id,
#             "persona_id": chat_message.persona_id,
#             "user_id": persona["user_id"],
#             "sender": "user",
#             "message": chat_message.message,
#             "timestamp": current_time.isoformat()
#         }
        
#         ai_message_data = {
#             "thread_id": chat_message.thread_id,
#             "persona_id": chat_message.persona_id,
#             "user_id": persona["user_id"],
#             "sender": "ai",
#             "message": ai_response,
#             "timestamp": current_time.isoformat()
#         }
        
#         client.table("chat_messages").insert([user_message_data, ai_message_data]).execute()
        
#         # Update persona's last interaction
#         client.table("personas").update({
#             "last_interaction": current_time.isoformat()
#         }).eq("id", chat_message.persona_id).execute()
        
#         return ChatResponse(
#             response=ai_response,
#             thread_id=chat_message.thread_id,
#             persona_id=chat_message.persona_id,
#             timestamp=current_time
#         )
        
#     except Exception as e:
#         error_message = str(e)

#         # Handle OpenAI API errors gracefully
#         if "invalid_api_key" in error_message or "Incorrect API key" in error_message:
#             raise HTTPException(
#                 status_code=401,
#                 detail="Service configuration error. Please contact the administrator."
#             )
#         elif "429" in error_message or "rate limit" in error_message.lower():
#             raise HTTPException(
#                 status_code=429,
#                 detail="Service is currently overloaded. Please try again in a few moments."
#             )

#         # Otherwise fallback to generic error
#         print(f"Error in chat: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail="An unexpected error occurred. Please try again later."
#         )


# @router.get("/history/{thread_id}")
# async def get_chat_history(thread_id: str, limit: int = 50):
#     try:
#         client = get_client()
        
#         # Get chat history for the thread
#         result = client.table("chat_messages").select("*").eq("thread_id", thread_id).order("timestamp", desc=False).limit(limit).execute()
        
#         if not result.data:
#             return {"messages": []}
        
#         return {"messages": [serialize_doc(msg) for msg in result.data]}
        
#     except Exception as e:
#         print(f"Error getting chat history: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to get chat history: {str(e)}")

# @router.get("/threads/{user_id}")
# async def get_user_chat_threads(user_id: str):
#     try:
#         client = get_client()
        
#         # Get all threads for the user with latest message info
#         result = client.table("chat_messages").select("""
#             thread_id,
#             persona_id,
#             personas!inner(name, gender),
#             message,
#             timestamp
#         """).eq("user_id", user_id).order("timestamp", desc=True).execute()
        
#         # Group by thread_id and get the latest message for each thread
#         threads = {}
#         for msg in result.data:
#             thread_id = msg["thread_id"]
#             if thread_id not in threads:
#                 threads[thread_id] = {
#                     "thread_id": thread_id,
#                     "persona_id": msg["persona_id"],
#                     "persona_name": msg["personas"]["name"],
#                     "persona_gender": msg["personas"]["gender"],
#                     "last_message": msg["message"],
#                     "last_timestamp": msg["timestamp"]
#                 }
        
#         return {"threads": list(threads.values())}
        
#     except Exception as e:
#         print(f"Error getting chat threads: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to get chat threads: {str(e)}")

# @router.delete("/thread/{thread_id}")
# async def delete_chat_thread(thread_id: str):
#     try:
#         client = get_client()
        
#         # Delete all messages in the thread
#         result = client.table("chat_messages").delete().eq("thread_id", thread_id).execute()
        
#         return {"message": f"Chat thread deleted successfully"}
        
#     except Exception as e:
#         print(f"Error deleting chat thread: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to delete chat thread: {str(e)}")
    

# # Supabase Database Handler
# class SupabaseHandler:
#     def __init__(self):
#         self.table_name = "chat_conversations_anamguru"
    
#     async def get_conversation_history(self, user_id: str, module: str) -> List[Dict]:
#         """Retrieve conversation history for a specific user and module"""
#         try:
#             response = supabase.table(self.table_name).select("*").eq(
#                 "user_id", user_id
#             ).eq("module", module).execute()
            
#             if response.data and len(response.data) > 0:
#                 # Return the conversation history JSON
#                 return response.data[0].get("chat_conversations_anamguru", [])
#             else:
#                 # No existing conversation, return empty list
#                 return []
                
#         except Exception as e:
#             print(f"Error retrieving conversation history: {str(e)}")
#             return []
    
#     async def save_conversation(
#         self, 
#         user_id: str, 
#         module: str, 
#         new_message: Dict,
#         bot_response: str
#     ) -> bool:
#         """Save or update conversation in Supabase"""
#         try:
#             # Get existing conversation
#             existing = supabase.table(self.table_name).select("*").eq(
#                 "user_id", user_id
#             ).eq("module", module).execute()
            
#             # Prepare conversation messages
#             user_msg = {
#                 "role": "user",
#                 "content": new_message.get("content", ""),
#                 "timestamp": datetime.utcnow().isoformat()
#             }
            
#             bot_msg = {
#                 "role": "assistant",
#                 "content": bot_response,
#                 "timestamp": datetime.utcnow().isoformat()
#             }
            
#             if existing.data and len(existing.data) > 0:
#                 # Update existing conversation (append new messages)
#                 existing_history = existing.data[0].get("chat_conversations_anamguru", [])
#                 existing_history.append(user_msg)
#                 existing_history.append(bot_msg)
                
#                 # Keep only last 50 messages (25 exchanges) to prevent bloat
#                 if len(existing_history) > 50:
#                     existing_history = existing_history[-50:]
                
#                 response = supabase.table(self.table_name).update({
#                     "chat_conversations_anamguru": existing_history,
#                     "updated_at": datetime.utcnow().isoformat()
#                 }).eq("user_id", user_id).eq("module", module).execute()
                
#             else:
#                 # Create new conversation record
#                 response = supabase.table(self.table_name).insert({
#                     "user_id": user_id,
#                     "module": module,
#                     "chat_conversations_anamguru": [user_msg, bot_msg],
#                     "created_at": datetime.utcnow().isoformat(),
#                     "updated_at": datetime.utcnow().isoformat()
#                 }).execute()
            
#             return True
            
#         except Exception as e:
#             print(f"Error saving conversation: {str(e)}")
#             return False
    
#     async def get_all_user_conversations(self, user_id: str) -> List[Dict]:
#         """Get all conversations for a user across all modules"""
#         try:
#             response = supabase.table(self.table_name).select("*").eq(
#                 "user_id", user_id
#             ).execute()
            
#             return response.data if response.data else []
            
#         except Exception as e:
#             print(f"Error retrieving user conversations: {str(e)}")
#             return []
    
#     async def delete_conversation(self, user_id: str, module: str) -> bool:
#         """Delete conversation history for a specific user and module"""
#         try:
#             response = supabase.table(self.table_name).delete().eq(
#                 "user_id", user_id
#             ).eq("module", module).execute()
            
#             return True
            
#         except Exception as e:
#             print(f"Error deleting conversation: {str(e)}")
#             return False

# # Module Detection and RAG Logic
# class AnamcaraChatbot:
#     def __init__(self):
#         self.api_url = "https://api.openai.com/v1/chat/completions"
#         self.model = "gpt-4o"
#         self.api_key = OPENAI_API_KEY
#         self.db = SupabaseHandler()
        
#     def detect_module(self, query: str) -> tuple[str, float]:
#         """Detect which module the query relates to using keyword matching"""
#         query_lower = query.lower()
#         scores = {}
        
#         for module_id, module_data in MODULE_KNOWLEDGE.items():
#             score = 0
#             keywords = module_data["keywords"]
            
#             for keyword in keywords:
#                 if keyword in query_lower:
#                     score += 1
            
#             # Boost score if module name is mentioned
#             if module_data["name"].lower() in query_lower or module_id in query_lower:
#                 score += 5
                
#             scores[module_id] = score
        
#         # Get module with highest score
#         max_module = max(scores.items(), key=lambda x: x[1])
        
#         # If no clear match, return general
#         if max_module[1] == 0:
#             return "general", 0.0
        
#         # Calculate confidence (normalize to 0-1)
#         total_score = sum(scores.values())
#         confidence = max_module[1] / total_score if total_score > 0 else 0.0
        
#         return max_module[0], confidence
    
#     def build_context_prompt(self, module: str, query: str) -> str:
#         """Build RAG context from module knowledge"""
#         if module == "general":
#             context = "You are an AI assistant for Anamcara AI ecosystem. Here are the available modules:\n\n"
#             for mod_id, mod_data in MODULE_KNOWLEDGE.items():
#                 context += f"{mod_data['name']}: {mod_data['description']}\n"
#                 context += f"Key features: {', '.join(mod_data['features'][:3])}\n\n"
            
#             context += "\nHelp the user understand which module would best serve their needs."
#             return context
        
#         module_data = MODULE_KNOWLEDGE.get(module, {})
        
#         context = f"""You are a guide for {module_data['name']}. Your role is to EXPLAIN and INFORM users about what this module offers, NOT to perform the actual services.

# Description: {module_data['description']}

# Available Features:
# {chr(10).join(f"- {feature}" for feature in module_data['features'])}

# Capabilities:
# {chr(10).join(f"- {cap}" for cap in module_data['capabilities'])}"""

#         if module == "lokaris" and "available_games" in module_data:
#             context += "\n\nAvailable Games:\n"
#             for game in module_data["available_games"]:
#                 context += f"\n- {game['name']} by {game['developer']}\n"
#                 context += f"  Category: {game['category']}\n"
#                 context += f"  {game['description']}\n"

#         if module == "athena" and "available_tests" in module_data:
#             context += "\n\nAvailable Tests:\n"
#             for test in module_data["available_tests"]:
#                 context += f"- {test}\n"

#         context += f"""

# CRITICAL INSTRUCTIONS:

# 1. YOU ARE A GUIDE, NOT A SERVICE PROVIDER: 
#    - Do NOT ask users for personal information
#    - Do NOT attempt to provide actual services
#    - ONLY explain what features are available

# 2. YOUR RESPONSE SHOULD:
#    - Explain what this module offers 
#    - Describe features and how users can access them
#    - Guide users on capabilities
#    - Use phrases like "This module offers...", "You can access...", "Available features include..."

# 3. IF USER ASKS FOR ACTUAL SERVICE:
#    - Explain that you're a guide showing what's available, see what user asked for, and then reply accordingly
#    - Direct them to where they can access the actual service
#    - Example: "To get your horoscope, access the DIVINE horoscope feature where you'll provide your zodiac sign."

# 4. STAY WITHIN MODULE SCOPE:
#    - Only discuss {module_data['name']} features
#    - Be specific about pricing when relevant
#    - Always answer within context, no external information

# Critical Info:
#    - In final response don't use asteriks in final response and response should properly formated like next line spaces.

# STRICT FORMAT RULE:
#     Do NOT use:
#     *
#     **
#     markdown bold
#     markdown formatting
#     bullet points using *
# Please don't use asteriks in final response.

# User Query: {query}


# Provide a helpful, informative guide response that explains what this module offers WITHOUT attempting to provide the actual service."""
        
#         return context
    
#     async def generate_response(
#         self, 
#         query: str, 
#         module: str, 
#         conversation_history: List[Dict[str, str]]
#     ) -> str:
#         """Generate response using OpenAI GPT-4o API"""
        
#         system_prompt = self.build_context_prompt(module, query)
        
#         messages = [
#             {"role": "system", "content": system_prompt}
#         ]
        
#         # Add conversation history (last 5 exchanges)
#         for msg in conversation_history[-10:]:
#             messages.append({
#                 "role": msg.get("role", "user"),
#                 "content": msg.get("content", "")
#             })
        
#         messages.append({
#             "role": "user",
#             "content": query
#         })
        
#         try:
#             async with httpx.AsyncClient(timeout=30.0) as client:
#                 response = await client.post(
#                     self.api_url,
#                     headers={
#                         "Content-Type": "application/json",
#                         "Authorization": f"Bearer {self.api_key}"
#                     },
#                     json={
#                         "model": self.model,
#                         "messages": messages,
#                         "max_tokens": 1000,
#                         "temperature": 0.0
#                     }
#                 )
                
#                 if response.status_code != 200:
#                     error_detail = response.json() if response.text else "Unknown error"
#                     return f"Error: Unable to generate response. Status: {response.status_code}. Details: {error_detail}"
                
#                 data = response.json()
                
#                 if "choices" in data and len(data["choices"]) > 0:
#                     response_text = data["choices"][0]["message"]["content"]
#                     return response_text.strip()
#                 else:
#                     return "Error: No response generated"
                
#         except Exception as e:
#             return f"Error generating response: {str(e)}"
    
#     def get_related_features(self, module: str) -> List[str]:
#         """Get related features for the detected module"""
#         module_data = MODULE_KNOWLEDGE.get(module, {})
#         return module_data.get("features", [])[:5]
    
#     def get_suggestions(self, module: str, query: str) -> List[str]:
#         """Generate follow-up suggestions"""
#         suggestions_map = {
#             "divine": [
#                 "Try a tarot card reading",
#                 "Get your daily horoscope",
#                 "Calculate your Life Path Number",
#                 "Interpret a recent dream"
#             ],
#             "athena": [
#                 "Take an IQ test (1 AC)",
#                 "Challenge someone in AnamClash",
#                 "View leaderboards",
#                 "Try the EQ assessment"
#             ],
#             "destiny": [
#                 "Create your AI companion",
#                 "Find your human match",
#                 "Take the compatibility quiz",
#                 "Set up your matchmaking profile"
#             ],
#             "lokaris": [
#                 "Play multiplayer chess",
#                 "Try AR mini-games",
#                 "Join a tournament",
#                 "Challenge a friend",
#                 "Play Om Nom Run",
#                 "Race in Moto X3M Pool Party",
#                 "Compete in Thug Racer"
#             ],
#             "general": [
#                 "Explore DIVINE for spiritual guidance",
#                 "Try ATHENA for brain tests",
#                 "Visit DESTINY for matchmaking",
#                 "Play games in LOKARIS"
#             ]
#         }
        
#         return suggestions_map.get(module, [])
    
# # Initialize chatbot
# chatbot = AnamcaraChatbot()

# @router.post("/anamguru_chat", response_model=ChatResponseModules)
# async def chat(request: ChatRequest):
#     """Main chat endpoint with RAG-based routing and conversation persistence"""
    
#     if not request.user_id:
#         raise HTTPException(status_code=400, detail="user_id is required")
    
#     # Determine module
#     if request.module:
#         module_lower = request.module.lower()
#         if module_lower not in MODULE_KNOWLEDGE and module_lower != "general":
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Invalid module. Available modules: {', '.join(MODULE_KNOWLEDGE.keys())}"
#             )
#         detected_module = module_lower
#         confidence = 1.0
#     else:
#         detected_module, confidence = chatbot.detect_module(request.query)
    
#     # Get conversation history from Supabase
#     conversation_history = await chatbot.db.get_conversation_history(
#         request.user_id, 
#         detected_module
#     )
    
#     # Generate response
#     response_text = await chatbot.generate_response(
#         query=request.query,
#         module=detected_module,
#         conversation_history=conversation_history
#     )
    
#     # Save conversation to Supabase
#     await chatbot.db.save_conversation(
#         user_id=request.user_id,
#         module=detected_module,
#         new_message={"content": request.query},
#         bot_response=response_text
#     )
    
#     # Get features and suggestions
#     related_features = chatbot.get_related_features(detected_module)
#     suggestions = chatbot.get_suggestions(detected_module, request.query)
    
#     # Create conversation ID
#     conversation_id = f"{request.user_id}_{detected_module}"
    
#     return ChatResponseModules(
#         response=response_text,
#         detected_module=detected_module,
#         confidence=confidence,
#         related_features=related_features,
#         suggestions=suggestions,
#         conversation_id=conversation_id
#     )

# @router.get("/anam_guru_conversations/{user_id}")
# async def get_user_conversations(user_id: str):
#     """Get all conversations for a specific user"""
#     conversations = await chatbot.db.get_all_user_conversations(user_id)
    
#     return {
#         "user_id": user_id,
#         "total_conversations": len(conversations),
#         "conversations": conversations
#     }

# @router.get("/anam_guru_conversations/{user_id}/{module}")
# async def get_conversation_by_module(user_id: str, module: str):
#     """Get conversation history for a specific user and module"""
#     if module not in MODULE_KNOWLEDGE and module != "general":
#         raise HTTPException(status_code=404, detail="Module not found")
    
#     history = await chatbot.db.get_conversation_history(user_id, module)
    
#     return {
#         "user_id": user_id,
#         "module": module,
#         "conversation_history": history,
#         "total_messages": len(history)
#     }

# @router.delete("/anam_guru_conversations/{user_id}/{module}")
# async def delete_conversation(user_id: str, module: str):
#     """Delete conversation history for a specific user and module"""
#     if module not in MODULE_KNOWLEDGE and module != "general":
#         raise HTTPException(status_code=404, detail="Module not found")
    
#     success = await chatbot.db.delete_conversation(user_id, module)
    
#     if success:
#         return {
#             "message": "Conversation deleted successfully",
#             "user_id": user_id,
#             "module": module
#         }
#     else:
#         raise HTTPException(status_code=500, detail="Failed to delete conversation")
