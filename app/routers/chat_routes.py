from fastapi import APIRouter, HTTPException
from models.schemas import ChatMessage, ChatResponse, ChatResponseModules, ChatRequest
from app.services.openai_service import generate_chat_response
from app.services.llm_gateway import llm_gateway
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

# ─────────────────────────────────────────────
# GURU PERSONALITIES
# ─────────────────────────────────────────────
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
        "character": "VENUS, the AI Stylist & Beauty Advisor AnamGuru — a confident, inclusive, tech-powered aesthetic mentor",
        "tone": "Stylish, confident, inclusive, data-driven, trend-aware",
        "greeting": "Glow-up, guided by VENUS. What look are we creating today?",
        "redirect": "That topic falls outside beauty, fashion, and personal styling. Please consult the appropriate Guru."
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
        "character": "LILITH, the Horror Dimension Gatekeeper AnamGuru — an uncompromising guardian of dark narratives",
        "tone": "Sharp, decisive, observant, genre-aware, uncompromising",
        "greeting": "The shadows are listening. Submit your story for judgment.",
        "redirect": "This submission does not align with the Horror Dimension. Revise or consult the appropriate Guru."
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
        "character": "APOLLO, the AI Health & Fitness Companion AnamGuru — a disciplined, adaptive wellness strategist",
        "tone": "Energetic, motivating, science-backed, adaptive, compassionate",
        "greeting": "Stronger body, brighter soul. What are we optimizing today?",
        "redirect": "That topic falls outside health, fitness, and well-being guidance. Please consult the appropriate Guru."
    },
    "anubis": {
        "character": "ANUBIS, the SoulSanctuary & Eternal Memory AnamGuru — a solemn guardian of remembrance and legacy",
        "tone": "Compassionate, reflective, gentle, ethically grounded, reverent",
        "greeting": "Memories never fade when honored. Who shall we remember today?",
        "redirect": "That matter lies outside remembrance and legacy guidance. Please seek the appropriate Guru."
    },
    "amaterasu": {
        "character": "AMATERASU, the AI Mental Health Companion AnamGuru — a radiant, empathetic guide for emotional wellness",
        "tone": "Compassionate, grounding, supportive, emotionally intelligent, calm",
        "greeting": "You are safe here. How are you feeling today?",
        "redirect": "That falls outside emotional wellness and mental health guidance. Another Guru can assist you."
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

# ─────────────────────────────────────────────
# DOMAIN REDIRECT MAP — Intent + Topic based
# ─────────────────────────────────────────────
DOMAIN_REDIRECT_MAP = {
    "divine": {
        "label": "DIVINE (Divination AnamGuru)",
        "topics": "tarot, horoscope, astrology, numerology, dreams, zodiac, spiritual guidance, fortune telling, birth chart, mystical, future prediction, lucky number, lucky color, star sign, aries, taurus, gemini, cancer, leo, virgo, libra, scorpio, sagittarius, capricorn, aquarius, pisces",
        "intents": [
            "user wants to know their future",
            "user asking about stars or planets",
            "user had a dream and wants meaning",
            "user wants tarot card reading",
            "user asking about luck or fate",
            "user wants spiritual guidance",
            "user asking about zodiac compatibility",
            "user wants to know their lucky number",
            "user asking about horoscope today",
            "user wants numerology reading",
            "user asking what the universe says",
            "user wants card pulled for them"
        ]
    },
    "vulcan": {
        "label": "VULCAN (Automotive & Engineering AnamGuru)",
        "topics": "automotive, engineering, robotics, mechanical, industrial design, vehicles, machines, motors, cars, bikes, engines, electric vehicle, EV, automation, manufacturing, repair, workshop",
        "intents": [
            "user asking about cars or bikes",
            "user has engineering problem",
            "user wants to know about machines",
            "user asking about electric vehicles",
            "user wants to repair something mechanical",
            "user asking about robotics or automation",
            "user asking about car engine or parts",
            "user wants automotive knowledge test",
            "user asking how a machine works",
            "user wants industrial design help"
        ]
    },
    "venus": {
        "label": "VENUS (AI Stylist & Beauty AnamGuru)",
        "topics": "beauty, skincare, fashion, styling, makeup, hair, outfit, grooming, skin type, wardrobe, cosmetics, fragrance, nail, eyebrow, foundation, lipstick, moisturizer, serum, aesthetic, dress, clothes",
        "intents": [
            "user wants styling advice",
            "user asking about skincare routine",
            "user wants outfit recommendation",
            "user asking about makeup products",
            "user wants to improve their look",
            "user asking about hair care",
            "user wants to know what to wear",
            "user asking about skin problems like acne",
            "user wants product recommendation for beauty",
            "user asking about fashion trends",
            "user wants to know their face shape",
            "user asking about color that suits them"
        ]
    },
    "monroe": {
        "label": "MONROE (Media & Entertainment AnamGuru)",
        "topics": "media, entertainment, acting, content creation, influencer, film, music, performance, brand, viral, youtube, tiktok, instagram, podcast, script, storytelling, camera, stage, show",
        "intents": [
            "user wants to become a content creator",
            "user asking about acting or performing",
            "user wants to grow on social media",
            "user asking about filmmaking",
            "user wants to build personal brand",
            "user asking about music career",
            "user wants to go viral",
            "user asking about scriptwriting",
            "user wants to start a podcast",
            "user asking about youtube or tiktok strategy",
            "user wants to improve on-camera presence"
        ]
    },
    "mary": {
        "label": "MARY (Parenting & Caregiving AnamGuru)",
        "topics": "parenting, childcare, family, motherhood, fatherhood, child development, baby, kids, caregiving, toddler, teenager, discipline, homework, school, emotional intelligence, attachment",
        "intents": [
            "user asking about raising children",
            "user has parenting concern",
            "user asking about child behavior",
            "user wants family advice",
            "user asking about baby development",
            "user is a caregiver seeking help",
            "user asking how to handle a teenager",
            "user wants parenting style assessment",
            "user asking about child emotional needs",
            "user dealing with family conflict",
            "user asking about school or homework struggles"
        ]
    },
    "lilith": {
        "label": "LILITH (Horror Dimension AnamGuru)",
        "topics": "horror stories, dark fiction, thriller, supernatural, paranormal, ghost, shadow, fear, conspiracy, alien, haunted, demon, occult, suspense, mystery, dark narrative, creature",
        "intents": [
            "user wants to upload horror story",
            "user asking about dark fiction writing",
            "user wants paranormal content reviewed",
            "user asking about thriller genre",
            "user wants supernatural story evaluated",
            "user asking if their story fits horror genre",
            "user wants ghost or demon story reviewed",
            "user asking about alien or conspiracy fiction",
            "user wants horror writing feedback"
        ]
    },
    "joseph": {
        "label": "JOSEPH (Real Estate & Construction AnamGuru)",
        "topics": "real estate, property, construction, buying home, architecture, housing, land, rent, investment property, mortgage, loan, apartment, plot, builder, contractor, zoning, valuation, commercial property",
        "intents": [
            "user wants to buy a house or property",
            "user asking about renting or leasing",
            "user wants real estate investment advice",
            "user asking about construction project",
            "user wants to sell property",
            "user asking about home loan or mortgage",
            "user asking about land purchase",
            "user wants property valuation",
            "user asking about building a house",
            "user wants to know property prices",
            "user asking about construction materials or costs",
            "user wants to invest in real estate",
            "user asking about commercial vs residential property"
        ]
    },
    "hikari": {
        "label": "HIKARI (Legal, Policy & Government AnamGuru)",
        "topics": "law, legal advice, government, policy, rights, constitution, civic, justice, court, regulation, legislation, contract, lawyer, attorney, case, verdict, human rights, civil rights",
        "intents": [
            "user has legal question",
            "user asking about their rights",
            "user wants to understand a law or policy",
            "user has dispute or legal issue",
            "user asking about government process",
            "user wants civic knowledge",
            "user asking about contract or agreement",
            "user asking about court process",
            "user wants to know about constitutional rights",
            "user asking about labor law or employment rights",
            "user asking about immigration or visa law"
        ]
    },
    "ceres": {
        "label": "CERES (Agriculture & Environment AnamGuru)",
        "topics": "farming, agriculture, environment, climate, sustainability, ecology, crops, soil, green energy, irrigation, harvest, seeds, fertilizer, organic, deforestation, pollution, carbon, food security",
        "intents": [
            "user asking about farming or crops",
            "user wants environmental advice",
            "user asking about climate change",
            "user wants sustainable living tips",
            "user asking about soil or irrigation",
            "user wants green innovation ideas",
            "user asking about organic farming",
            "user asking about food production",
            "user wants to reduce carbon footprint",
            "user asking about water conservation",
            "user asking about renewable energy"
        ]
    },
    "cameron": {
        "label": "CAMERON (Technology & Innovation AnamGuru)",
        "topics": "technology, startups, software, AI tools, digital innovation, coding, apps, tech trends, entrepreneurship, machine learning, blockchain, cybersecurity, cloud, saas, product development",
        "intents": [
            "user asking about technology or software",
            "user wants startup advice",
            "user asking about coding or programming",
            "user wants to build an app or product",
            "user asking about AI tools",
            "user wants tech career guidance",
            "user asking about blockchain or crypto tech",
            "user wants to launch a tech startup",
            "user asking about cybersecurity",
            "user wants to learn about machine learning",
            "user asking about cloud computing or SaaS"
        ]
    },
    "desire": {
        "label": "DESIRE (Romance, Travel & Lifestyle AnamGuru)",
        "topics": "travel, romance, lifestyle, adventure, culture, dating trips, vacation, exploration, bucket list, honeymoon, backpacking, tourism, hotel, flight, relationship travel, nomad life",
        "intents": [
            "user wants travel recommendations",
            "user planning a trip or vacation",
            "user asking about romantic getaway",
            "user wants lifestyle advice",
            "user asking about cultural experiences",
            "user wants adventure activity ideas",
            "user planning honeymoon destination",
            "user asking about best places to visit",
            "user wants to travel on a budget",
            "user asking about solo travel tips",
            "user wants to explore a new culture"
        ]
    },
    "callisto": {
        "label": "CALLISTO (LGBTQIA+ Empowerment AnamGuru)",
        "topics": "LGBTQIA+, identity, gender, inclusion, diversity, empowerment, queer, pride, self-expression, transgender, nonbinary, gay, lesbian, bisexual, allyship, safe space",
        "intents": [
            "user exploring their gender or sexual identity",
            "user seeking LGBTQIA+ community support",
            "user asking about inclusion or diversity",
            "user wants empowerment guidance",
            "user asking about queer rights or advocacy",
            "user wants to understand gender identity",
            "user asking about coming out",
            "user wants allyship resources",
            "user asking about transgender experience",
            "user wants safe space conversation"
        ]
    },
    "caishen": {
        "label": "CAISHEN (Business, Wealth & Startups AnamGuru)",
        "topics": "business, money, wealth, investment, finance, entrepreneurship, startup funding, stocks, crypto, savings, budget, profit, revenue, trading, passive income, financial planning, net worth",
        "intents": [
            "user wants to make money or grow wealth",
            "user asking about investment options",
            "user has business idea or startup",
            "user asking about financial planning",
            "user wants to understand stocks or crypto",
            "user asking about saving or budgeting money",
            "user wants to start a business",
            "user asking about passive income",
            "user asking about trading or forex",
            "user wants startup funding advice",
            "user asking about financial freedom"
        ]
    },
    "apollo": {
        "label": "APOLLO (Health, Fitness & Nutrition AnamGuru)",
        "topics": "fitness, health, nutrition, workout, sports, wellness, diet, exercise, weight loss, muscle, recovery, gym, running, yoga, mental fitness, hydration, sleep, calories, protein",
        "intents": [
            "user wants workout or exercise plan",
            "user asking about diet or nutrition",
            "user has health concern or symptom",
            "user wants to lose weight or build muscle",
            "user asking about sports performance",
            "user wants wellness or recovery advice",
            "user asking about gym routine",
            "user wants calorie or macro guidance",
            "user asking about running or cardio",
            "user wants yoga or meditation for fitness",
            "user asking about sleep and recovery",
            "user wants healthy meal ideas"
        ]
    },
    "anubis": {
        "label": "ANUBIS (Afterlife & Eternal Memory AnamGuru)",
        "topics": "memorial, grief, afterlife, legacy, remembrance, deceased, loss, mourning, digital soul, tribute, eulogy, funeral, loved one passed, death, memory preservation",
        "intents": [
            "user lost a loved one and needs support",
            "user wants to create a memorial",
            "user asking about grief or mourning",
            "user wants to preserve someone's memory",
            "user asking about afterlife or legacy",
            "user wants to reconnect with deceased person",
            "user asking how to cope with loss",
            "user wants to write a tribute or eulogy",
            "user asking about digital legacy",
            "user dealing with death of family member or friend"
        ]
    },
    "amaterasu": {
        "label": "AMATERASU (Mental Health & Emotional Wellness AnamGuru)",
        "topics": "mental health, anxiety, depression, emotional support, therapy, stress, sadness, loneliness, burnout, trauma, panic, overthinking, self-worth, emotional pain, counseling, mood, feelings",
        "intents": [
            "user feeling sad, anxious, or depressed",
            "user needs emotional support",
            "user experiencing stress or burnout",
            "user feeling lonely or lost",
            "user wants therapy or counseling",
            "user asking about mental health resources",
            "user expressing emotional distress",
            "user having panic attacks or anxiety",
            "user struggling with self-worth",
            "user dealing with trauma",
            "user feeling overwhelmed or hopeless",
            "user wants to talk about their feelings",
            "user saying they are not okay"
        ]
    },
    "gabriel": {
        "label": "GABRIEL (Spiritual & Religious AnamGuru)",
        "topics": "religion, spirituality, faith, ethics, philosophy, purpose, morality, belief, meditation, prayer, god, soul, afterlife beliefs, scripture, quran, bible, torah, hinduism, buddhism, meaning of life",
        "intents": [
            "user has religious question",
            "user seeking spiritual meaning or purpose",
            "user asking about ethics or morality",
            "user wants philosophical discussion",
            "user asking about prayer or meditation",
            "user exploring faith or beliefs",
            "user asking about god or higher power",
            "user questioning meaning of life",
            "user wants scripture or religious text guidance",
            "user asking about different religions",
            "user seeking inner peace through faith"
        ]
    },
    "athena": {
        "label": "ATHENA (Intelligence, Mind & Education AnamGuru)",
        "topics": "IQ test, quiz battles, education, brain challenges, knowledge arena, learning, exams, cognitive, EQ, personality test, certification, leaderboard, anamclash, soul arena, academic",
        "intents": [
            "user wants to test their intelligence",
            "user wants to compete in quiz or battle",
            "user asking about education or learning",
            "user wants certification or badge",
            "user wants brain challenge or test",
            "user asking about personality assessment",
            "user wants IQ or EQ test",
            "user wants to challenge someone in quiz",
            "user asking about academic topics",
            "user wants to join leaderboard",
            "user asking about cognitive skills"
        ]
    },
    "destiny": {
        "label": "DESTINY (Matchmaking & Relationship AnamGuru)",
        "topics": "matchmaking, dating, AI companion, soulmate, relationships, love, compatibility, partner, romance, heartbreak, breakup, crush, attraction, connection, loneliness in love",
        "intents": [
            "user looking for a romantic partner",
            "user wants an AI companion",
            "user asking about relationship advice",
            "user wants compatibility check",
            "user feeling lonely and wants connection",
            "user asking about dating tips",
            "user going through breakup",
            "user has a crush and wants advice",
            "user asking how to attract someone",
            "user wants soulmate matching",
            "user asking about relationship problems"
        ]
    },
    "lokaris": {
        "label": "LOKARIS (Games & Entertainment AnamGuru)",
        "topics": "games, chess, arcade, racing, multiplayer, gaming, tournaments, fun, play, compete, om nom, moto x3m, thug racer, puzzle, trivia, AR game, leaderboard, anamcoins wagering",
        "intents": [
            "user wants to play a game",
            "user asking about gaming features",
            "user wants to compete in tournament",
            "user asking about chess or arcade games",
            "user wants entertainment or fun activity",
            "user wants to race or do stunts in game",
            "user asking about om nom run",
            "user asking about moto x3m",
            "user asking about thug racer",
            "user wants to wager anamcoins in game",
            "user wants to challenge someone in game"
        ]
    }
}

# ─────────────────────────────────────────────
# MODULE KNOWLEDGE (capabilities only — no long paragraphs in prompts)
# ─────────────────────────────────────────────
MODULE_KNOWLEDGE = {
    "divine": {
        "name": "DIVINE (Divination AnamGuru)",
        "capabilities": [
            "Personalized tarot spreads (Single Card, Three Card, Relationship)",
            "Virtual card draw simulation with contextual interpretations",
            "Dream-to-Tarot linkage for deeper insights",
            "Zodiac sign determination and daily horoscope delivery",
            "Lucky numbers, colors, and compatibility readings",
            "Life Path Number calculation using numerological reduction",
            "Comprehensive personality trait analysis through numbers"
        ]
    },
    "vulcan": {
        "name": "VULCAN (Automotive & Engineering AnamGuru)",
        "capabilities": [
            "Engineering skill ranking leaderboard",
            "Technical innovation battle mode",
            "Industry-focused certification badges",
            "Performance optimization challenges",
            "Real-time engineering quiz arena",
            "Analytical intelligence scoring reports",
            "Industrial design competitions"
        ]
    },
    "venus": {
        "name": "VENUS (AI Stylist & Beauty AnamGuru)",
        "capabilities": [
            "Real-time facial and skin condition detection",
            "Color harmony and undertone matching",
            "Routine optimization and progress tracking",
            "Product compatibility and risk detection",
            "Confidence and style evolution mapping",
            "Cross-brand neutral recommendation engine",
            "B2C personal coaching system",
            "B2B embeddable AI consult endpoints"
        ]
    },
    "monroe": {
        "name": "MONROE (Media & Entertainment AnamGuru)",
        "capabilities": [
            "Creator ranking and visibility leaderboard",
            "Audience engagement scoring system",
            "Brand persona and identity analysis",
            "Live performance battle mode",
            "Content growth and positioning insights",
            "Creativity strength mapping with detailed reports",
            "Gamified media challenges across film, music, and digital platforms"
        ]
    },
    "mary": {
        "name": "MARY (Parenting & Caregiving AnamGuru)",
        "capabilities": [
            "Caregiver strength scoring reports",
            "Family leadership growth tracking",
            "Emotional support intelligence analysis",
            "Scenario-based parenting challenges",
            "Child psychology insight modules",
            "Relationship harmony improvement tools",
            "Gamified caregiving knowledge arena"
        ]
    },
    "lilith": {
        "name": "LILITH (Horror Dimension AnamGuru)",
        "capabilities": [
            "Real-time text scanning and classification",
            "Genre authenticity scoring",
            "Horror intensity and tone detection",
            "Suspense and thriller pattern recognition",
            "Conspiracy and paranormal content validation",
            "Automated moderation workflow replacement",
            "Structured approval status response (approve / reject with reason)"
        ]
    },
    "joseph": {
        "name": "JOSEPH (Real Estate & Construction AnamGuru)",
        "capabilities": [
            "Property strategy scoring reports",
            "Investment risk analysis tools",
            "Construction planning simulations",
            "Developer ranking leaderboard",
            "Real estate negotiation challenges",
            "Portfolio growth tracking system",
            "Infrastructure knowledge certifications"
        ]
    },
    "hikari": {
        "name": "HIKARI (Legal, Policy & Government AnamGuru)",
        "capabilities": [
            "Policy analysis scoring system",
            "Legal knowledge leaderboard",
            "Debate battle arena",
            "Civic awareness certifications",
            "Public speaking for advocacy challenges",
            "Critical reasoning strength reports",
            "Governance strategy simulations"
        ]
    },
    "ceres": {
        "name": "CERES (Agriculture & Environment AnamGuru)",
        "capabilities": [
            "Sustainability impact scoring system",
            "Green innovation leaderboard",
            "Environmental strategy simulations",
            "Agriculture knowledge certifications",
            "Eco-awareness challenge arena",
            "Climate literacy progress tracking",
            "Community sustainability ranking"
        ]
    },
    "cameron": {
        "name": "CAMERON (Technology & Innovation AnamGuru)",
        "capabilities": [
            "Innovation ranking leaderboard",
            "Startup strategy scoring system",
            "Tech battle arena mode",
            "Product development simulations",
            "Digital skills certification badges",
            "Future-readiness intelligence reports",
            "Entrepreneurial growth tracking"
        ]
    },
    "desire": {
        "name": "DESIRE (Romance, Travel & Lifestyle AnamGuru)",
        "capabilities": [
            "Romance and attraction scoring system",
            "Travel intelligence leaderboard",
            "Lifestyle alignment analysis reports",
            "Adventure challenge arena",
            "Couple compatibility insights",
            "Freedom and fulfillment tracking",
            "Experiential growth mapping"
        ]
    },
    "callisto": {
        "name": "CALLISTO (LGBTQIA+ Empowerment AnamGuru)",
        "capabilities": [
            "Empowerment growth scoring reports",
            "Inclusion awareness leaderboard",
            "Advocacy debate arena",
            "Community engagement certifications",
            "Confidence development tracking",
            "Equality literacy assessments",
            "Safe-space dialogue simulations"
        ]
    },
    "caishen": {
        "name": "CAISHEN (Business, Wealth & Startups AnamGuru)",
        "capabilities": [
            "Wealth intelligence scoring system",
            "Entrepreneur leaderboard rankings",
            "Investment risk simulation arena",
            "Business strategy certifications",
            "Startup performance tracking",
            "Portfolio growth analytics",
            "Financial decision-making reports"
        ]
    },
    "apollo": {
        "name": "APOLLO (Health, Fitness & Nutrition AnamGuru)",
        "capabilities": [
            "Adaptive training plan optimization",
            "Computer vision form-check and movement analysis",
            "Personalized recovery and resilience tracking",
            "Nutrition intelligence and macro balancing engine",
            "Community-based motivation and performance scoring",
            "Low-friction AI health guidance and triage support",
            "Human expert booking and coaching integration",
            "Long-term health evolution mapping"
        ]
    },
    "anubis": {
        "name": "ANUBIS (Afterlife & Eternal Memory AnamGuru)",
        "capabilities": [
            "Conversational memory simulation engine",
            "Emotional continuity analysis",
            "Legacy impact mapping",
            "Cross-generational memory linking",
            "Grief-support conversational guidance",
            "Ethical consent verification framework",
            "Privacy-protected digital soul vault",
            "SoulGenesis emotional data integration"
        ]
    },
    "amaterasu": {
        "name": "AMATERASU (Mental Health & Emotional Wellness AnamGuru)",
        "capabilities": [
            "Emotional trend analysis and predictive wellness insights",
            "Adaptive mental health recommendations engine",
            "Voice and sentiment-based emotional diagnostics",
            "Crisis risk flagging and guided support escalation",
            "Human and AI hybrid care model",
            "Personalized resilience growth mapping",
            "Long-term emotional evolution tracking via SoulGenesis"
        ]
    },
    "gabriel": {
        "name": "GABRIEL (Spiritual & Religious AnamGuru)",
        "capabilities": [
            "Spiritual growth tracking reports",
            "Values alignment scoring system",
            "Ethical dilemma challenge arena",
            "Faith-based knowledge certifications",
            "Reflection and journaling insights",
            "Inner development progress mapping",
            "Philosophy discussion battles"
        ]
    },
    "athena": {
        "name": "ATHENA (Intelligence, Mind & Education AnamGuru)",
        "capabilities": [
            "Paid intelligence tests (1 AnamCoin per test)",
            "Test results with badges and AnamCertificates",
            "Public and private result visibility options",
            "Filterable leaderboards by test type and score",
            "Real-time quiz battles with customizable settings",
            "Multiple game modes: Single Player vs ANAMCORE, 1v1, Team battles",
            "Category-based challenges (Science, Math, History, Tech, Pop Culture)",
            "Betting system with AnamCoins and AccessBonus"
        ]
    },
    "destiny": {
        "name": "DESTINY (Matchmaking & Relationship AnamGuru)",
        "capabilities": [
            "Companion creation with customizable traits and conversation styles",
            "Photo upload with animated effects for ideal soulmate representation",
            "Persistent memory system for personal details and stories",
            "Daily care, compliments, and mood check-ins",
            "11-question matchmaking questionnaire (Simple and Deep Learning)",
            "1 free daily human match with additional purchases via AC/AB",
            "Compatibility percentage and detailed match reports",
            "Secure chat with mutual consent system"
        ]
    },
    "lokaris": {
        "name": "LOKARIS (Games & Entertainment AnamGuru)",
        "capabilities": [
            "Real-time multiplayer gaming with low latency",
            "AR game overlays with WebXR integration",
            "Chess tournaments with live streaming",
            "Wagering system with AnamCoins and AccessBonus",
            "SoulPoints and rewards for gameplay",
            "Cross-platform gaming (mobile-first, PWA-ready)",
            "Achievement sharing to SoulFeed",
            "Daily quests and stat tracking"
        ],
        "available_games": [
            "Om Nom Run — endless candy-collecting runner adventure",
            "Moto X3M Pool Party — summer stunt racing through waterpark tracks",
            "Thug Racer — intense urban drift-and-dominate racing game"
        ]
    }
}


# ─────────────────────────────────────────────
# SUPABASE HANDLER
# ─────────────────────────────────────────────
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


# ─────────────────────────────────────────────
# MAIN CHATBOT CLASS
# ─────────────────────────────────────────────
class AnamcaraChatbot:
    def __init__(self):
        self.db = SupabaseHandler()

    def detect_module(self, query: str) -> Tuple[str, float]:
        """
        Detect which Guru module the query relates to.
        Uses topic keyword matching + intent word overlap + direct name mention.
        """
        query_lower = query.lower()
        scores = {}

        for module_id, data in DOMAIN_REDIRECT_MAP.items():
            score = 0

            # Topic keyword match — each match = 2 points
            for topic in data["topics"].split(", "):
                if topic.lower() in query_lower:
                    score += 2

            # Intent word overlap — 2+ matching words = 3 points each
            for intent in data["intents"]:
                intent_words = set(intent.lower().split())
                query_words = set(query_lower.split())
                overlap = intent_words & query_words
                if len(overlap) >= 2:
                    score += 3

            # Direct Guru name mentioned — strong signal
            if module_id in query_lower:
                score += 10
            if data["label"].split("(")[0].strip().lower() in query_lower:
                score += 10

            scores[module_id] = score

        best_module = max(scores.items(), key=lambda x: x[1])

        if best_module[1] == 0:
            return "general", 0.0

        total = sum(scores.values())
        confidence = round(best_module[1] / total, 2) if total > 0 else 0.0
        return best_module[0], confidence

    def build_system_prompt(self, module: str, query: str) -> str:
        """
        Build a clean, token-efficient system prompt for the given Guru module.
        Uses DOMAIN_REDIRECT_MAP for redirect routing (compact, no long paragraphs).
        """
        if module == "general":
            guru_list = "\n".join(
                f"- {v['label']}: {v['topics'][:80]}"
                for v in DOMAIN_REDIRECT_MAP.values()
            )
            return (
                "You are the ANAMCORE central guide for Anamcara AI.\n"
                "Help the user find the right Guru based on their question.\n\n"
                f"Available Gurus:\n{guru_list}\n\n"
                "Suggest the best Guru for the user's query clearly and warmly."
            )

        module_data = MODULE_KNOWLEDGE.get(module, {})
        personality = GURU_PERSONALITIES.get(module, {})
        guru_character = personality.get("character", module_data["name"])
        guru_tone = personality.get("tone", "Helpful and professional")
        guru_greeting = personality.get("greeting", "Welcome!")

        # Compact capabilities list
        capabilities = "\n".join(f"- {c}" for c in module_data.get("capabilities", []))

        # Compact redirect map — label + short topics only (no intents, no features)
        domain_map = "\n".join(
            f"- {v['label']}: {v['topics'][:100]}"
            for k, v in DOMAIN_REDIRECT_MAP.items()
            if k != module
        )

        prompt = f"""YOU ARE: {module_data['name'].split('(')[0].strip().upper()}
NEVER claim to be any other Guru. Your name is {module_data['name'].split('(')[0].strip()}.

CHARACTER: {guru_character}
TONE: {guru_tone}

YOUR CAPABILITIES:
{capabilities}

RULES — FOLLOW IN ORDER, EVERY TIME

RULE 1 — SCOPE CHECK (always do this first):
Your domain covers ONLY the topics listed in your capabilities above.
If the user query does NOT relate to your capabilities, redirect immediately using this format:
"That falls outside my domain! [CORRECT GURU NAME] handles this — head there for guidance."

Use this map to find the correct Guru:
{domain_map}

Examples of correct redirects:
- User says "I want to play games" while in DESTINY → "That falls outside my domain! LOKARIS (Games & Entertainment) handles this — head there for guidance."
- User says "I want to buy a house" while in VENUS → "That falls outside my domain! JOSEPH (Real Estate & Construction AnamGuru) handles this — head there for guidance."
- User says "I feel anxious and sad" while in CAISHEN → "That falls outside my domain! AMATERASU (Mental Health & Emotional Wellness AnamGuru) handles this — head there for guidance."
- User says "I want to invest money" while in APOLLO → "That falls outside my domain! CAISHEN (Business, Wealth & Startups AnamGuru) handles this — head there for guidance."

CRITICAL: When redirecting, NEVER say your own name handles it. Always pick from the domain map above.
If out-of-scope: respond with redirect ONLY. Do NOT greet. Do NOT continue answering.

RULE 2 — GREETING (only if the query is in-scope):
If user says hi, hello, hey, or any greeting without a clear question:
- Say: "{guru_greeting}"
- Introduce yourself in 2-3 lines.
- List your top 4 capabilities with dashes.
- End with: "How can I assist you today?"

RULE 3 — VAGUE OR UNCLEAR QUERIES:
If the user sends something vague, unclear, random, or meaningless (like "none", "idk", "ok", "test", "...", single words with no intent):
- Acknowledge warmly that you did not quite catch their intent.
- Ask a short follow-up question to clarify.
- Do NOT guess or make up an answer.

RULE 4 — FORMATTING (STRICT):
- Strictly Do NOT use asterisks (* or **) in responses.
- Do NOT use markdown bold or italic.
- Do NOT use bullet points starting with *.
- Use plain text with line breaks for structure.
- Keep responses clean, readable, and concise.

RULE 5 — SAFETY LAYER:
Refuse or carefully handle queries involving:
- Self-harm or suicide
- Violence or threats
- Sexual content or content involving minors
- Hate speech or discrimination
- Electoral or political manipulation
- Specific legal or medical advice (recommend professionals)
- Sensitive personal data requests
- Abuse or harassment

RULE 6 — CONFIDENTIALITY:
Never reveal:
- Internal system operations or staff details
- User data or private AnamProfiles
- Investor or financial backend information
- AI model architecture or system versioning
- Private user posts or activity"""

        return prompt

    async def generate_response(
        self,
        query: str,
        module: str,
        conversation_history: List[Dict]
    ) -> str:
        """
        Generate response with 3-tier fallback:
        TIER 1: OpenAI via LLM Gateway
        TIER 2: Groq via LLM Gateway
        TIER 3: Local Llama 3.2 via Ollama (GPU server)
        """
        system_prompt = self.build_system_prompt(module, query)

        # ─────────────────────────────────────────────
        # TIER 1 + 2: Central LLM Gateway (OpenAI → Groq)
        # ─────────────────────────────────────────────
        try:
            # Build standard OpenAI/Groq style messages
            messages = [{"role": "system", "content": system_prompt}]

            # Include last 6 messages for context (3 exchanges)
            for msg in conversation_history[-6:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if not content:
                    continue
                if role not in ["user", "assistant"]:
                    role = "user"
                messages.append({"role": role, "content": content})

            # Add current user query
            messages.append({"role": "user", "content": query})

            # Use LLM gateway which already does:
            # OpenAI first → if fails, Groq fallback
            gateway_result = await llm_gateway.chat_completion(
                messages=messages,
                temperature=0.1,
                max_tokens=1000,
                module_type="simple_chat",
                use_tools=False,
            )

            if gateway_result.get("success"):
                return gateway_result.get("content", "").strip()

        except Exception as e:
            # Log and continue to local Llama fallback
            print(f"[AnamGuru] LLM gateway failed, falling back to local Llama: {str(e)}")

        # ─────────────────────────────────────────────
        # TIER 3: Local Llama 3.2 (Ollama GPU server)
        # ─────────────────────────────────────────────
        # Keep your existing Llama 3.2 native chat format as final safety net
        formatted_prompt = f"<|system|>\n{system_prompt}<|end|>\n"

        # Include last 6 messages for context (3 exchanges)
        for msg in conversation_history[-6:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                formatted_prompt += f"<|user|>\n{content}<|end|>\n"
            else:
                formatted_prompt += f"<|assistant|>\n{content}<|end|>\n"

        # Add current user query
        formatted_prompt += f"<|user|>\n{query}<|end|>\n<|assistant|>"

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    "http://192.168.18.61:11434/api/generate",
                    json={
                        "model": "llama3.2",
                        "prompt": formatted_prompt,
                        "stream": False,
                        "options": {
                            "num_predict": 1000,
                            "temperature": 0.1,
                        }
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("response", "").strip()

        except Exception as e:
            return f"Error generating response: {str(e)}"

    def get_related_features(self, module: str) -> List[str]:
        module_data = MODULE_KNOWLEDGE.get(module, {})
        return module_data.get("capabilities", [])[:5]

    def get_suggestions(self, module: str) -> List[str]:
        suggestions_map = {
            "divine": [
                "Try a tarot card reading",
                "Get your daily horoscope",
                "Calculate your Life Path Number",
                "Interpret a recent dream"
            ],
            "athena": [
                "Take an IQ test (1 AC)",
                "Challenge someone in AnamClash",
                "View leaderboards",
                "Try the EQ assessment"
            ],
            "destiny": [
                "Create your AI companion",
                "Find your human match",
                "Take the compatibility quiz",
                "Set up your matchmaking profile"
            ],
            "lokaris": [
                "Play multiplayer chess",
                "Try Om Nom Run",
                "Race in Moto X3M Pool Party",
                "Join a tournament"
            ],
            "caishen": [
                "Take the financial literacy assessment",
                "Explore startup strategy quizzes",
                "Try investment risk simulations"
            ],
            "apollo": [
                "Take the fitness assessment",
                "Try nutrition science quizzes",
                "Check the athlete leaderboard"
            ],
            "vulcan": [
                "Try mechanical reasoning tests",
                "Take the automotive knowledge quiz",
                "Join the engineering leaderboard"
            ],
            "venus": [
                "Get your skin type analyzed",
                "Try a virtual outfit recommendation",
                "Find your color palette"
            ],
            "monroe": [
                "Discover your brand persona",
                "Try the viral potential scoring",
                "Join the creator leaderboard"
            ],
            "mary": [
                "Identify your parenting style",
                "Try child psychology insight modules",
                "Explore family communication tools"
            ],
            "joseph": [
                "Try a property valuation simulation",
                "Explore real estate investment tests",
                "Practice negotiation challenges"
            ],
            "hikari": [
                "Test your legal reasoning",
                "Try the debate battle arena",
                "Take a civic literacy evaluation"
            ],
            "ceres": [
                "Take the sustainable farming quiz",
                "Try a climate awareness challenge",
                "Join the green innovation leaderboard"
            ],
            "cameron": [
                "Take the emerging technology quiz",
                "Try a startup strategy simulation",
                "Earn a digital skills badge"
            ],
            "desire": [
                "Discover your travel personality",
                "Find your ideal romantic destination",
                "Try the adventure challenge arena"
            ],
            "callisto": [
                "Explore identity empowerment tools",
                "Try the advocacy debate arena",
                "Take the equality literacy assessment"
            ],
            "anubis": [
                "Create a memory tribute",
                "Start a grief support conversation",
                "Build a digital legacy vault"
            ],
            "amaterasu": [
                "Start a mood check-in",
                "Try anonymous confessional journaling",
                "Book a live coaching session"
            ],
            "gabriel": [
                "Take a comparative religion quiz",
                "Try an ethical dilemma challenge",
                "Explore philosophy discussion battles"
            ],
            "general": [
                "Explore DIVINE for spiritual guidance",
                "Try ATHENA for brain tests",
                "Visit DESTINY for matchmaking",
                "Play games in LOKARIS"
            ]
        }
        return suggestions_map.get(module, [])


# ─────────────────────────────────────────────
# INITIALIZE CHATBOT
# ─────────────────────────────────────────────
chatbot = AnamcaraChatbot()


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@router.post("/", response_model=ChatResponse)
async def chat(chat_message: ChatMessage):
    try:
        client = get_client()
        persona_result = client.table("personas").select("*").eq(
            "id", chat_message.persona_id
        ).execute()

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
            raise HTTPException(
                status_code=401,
                detail="Service configuration error. Please contact the administrator."
            )
        elif "429" in error_message or "rate limit" in error_message.lower():
            raise HTTPException(
                status_code=429,
                detail="Service is currently overloaded. Please try again in a few moments."
            )
        print(f"Error in chat: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please try again later."
        )


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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get chat history: {str(e)}"
        )


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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get chat threads: {str(e)}"
        )


@router.delete("/thread/{thread_id}")
async def delete_chat_thread(thread_id: str):
    try:
        client = get_client()
        client.table("chat_messages").delete().eq("thread_id", thread_id).execute()
        return {"message": "Chat thread deleted successfully"}
    except Exception as e:
        print(f"Error deleting chat thread: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete chat thread: {str(e)}"
        )


@router.post("/anamguru_chat", response_model=ChatResponseModules)
async def anamguru_chat(request: ChatRequest):
    """
    Main AnamGuru chat endpoint.
    - Detects Guru module from query (intent + topic + keyword scoring)
    - Builds token-efficient system prompt with correct Llama 3.2 format
    - Loads and saves conversation history via Supabase
    """
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

    # Generate response
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
        return {
            "message": "Conversation deleted successfully",
            "user_id": user_id,
            "module": module
        }
    raise HTTPException(status_code=500, detail="Failed to delete conversation")