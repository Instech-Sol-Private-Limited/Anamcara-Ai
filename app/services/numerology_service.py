

# app/services/numerology_service.py
import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load meanings from JSON
with open("app/data/numerology_meanings.json") as f:
    meanings = json.load(f)


# ---------- Core Numerology Calculations ----------
def reduce_number(n):
    if n in [11, 22, 33]:  # Master numbers
        return n
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


def life_path(dob):
    digits = [int(c) for c in dob if c.isdigit()]
    return reduce_number(sum(digits))


def expression(name):
    values = {c: (ord(c) - 64) % 9 or 9 for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}
    return reduce_number(sum(values.get(c, 0) for c in name.upper() if c.isalpha()))


def soul_urge(name):
    vowels = "AEIOU"
    values = {c: (ord(c) - 64) % 9 or 9 for c in vowels}
    return reduce_number(sum(values.get(c, 0) for c in name.upper() if c in vowels))

from app.services.llm_gateway import llm_gateway
import asyncio
from datetime import datetime

# Core numerology calculation functions (PRESERVED - DO NOT CHANGE)
def reduce_to_single_digit(n: int) -> int:
    """Reduce number to single digit (except master numbers 11, 22, 33)"""
    while n > 9 and n not in [11, 22, 33]:
        n = sum(int(digit) for digit in str(n))
    return n

def life_path(dob: str) -> int:
    """
    Calculate Life Path number from date of birth
    Format: YYYY-MM-DD or MM/DD/YYYY
    """
    try:
        # Handle different date formats
        if '/' in dob:
            parts = dob.split('/')
            if len(parts[2]) == 4:  # MM/DD/YYYY
                month, day, year = int(parts[0]), int(parts[1]), int(parts[2])
            else:  # DD/MM/YYYY
                day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
        elif '-' in dob:
            parts = dob.split('-')
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        else:
            raise ValueError("Invalid date format")
        
        # Reduce each component
        month_sum = reduce_to_single_digit(month)
        day_sum = reduce_to_single_digit(day)
        year_sum = reduce_to_single_digit(sum(int(d) for d in str(year)))
        
        # Add and reduce final
        total = month_sum + day_sum + year_sum
        return reduce_to_single_digit(total)
    
    except Exception as e:
        print(f"Error calculating life path: {e}")
        return 1  # Default fallback

def expression(name: str) -> int:
    """
    Calculate Expression (Destiny) number from full name
    Uses Pythagorean numerology system
    """
    letter_values = {
        'A': 1, 'J': 1, 'S': 1,
        'B': 2, 'K': 2, 'T': 2,
        'C': 3, 'L': 3, 'U': 3,
        'D': 4, 'M': 4, 'V': 4,
        'E': 5, 'N': 5, 'W': 5,
        'F': 6, 'O': 6, 'X': 6,
        'G': 7, 'P': 7, 'Y': 7,
        'H': 8, 'Q': 8, 'Z': 8,
        'I': 9, 'R': 9
    }
    
    total = 0
    for char in name.upper():
        if char in letter_values:
            total += letter_values[char]
    
    return reduce_to_single_digit(total)

def soul_urge(name: str) -> int:
    """
    Calculate Soul Urge (Heart's Desire) number from vowels in name
    """
    vowels = 'AEIOU'
    letter_values = {
        'A': 1, 'E': 5, 'I': 9, 'O': 6, 'U': 3
    }
    
    total = 0
    for char in name.upper():
        if char in vowels:
            total += letter_values[char]
    
    return reduce_to_single_digit(total)

def personality(name: str) -> int:
    """
    Calculate Personality number from consonants in name
    """
    vowels = 'AEIOU'
    letter_values = {
        'B': 2, 'C': 3, 'D': 4, 'F': 6, 'G': 7,
        'H': 8, 'J': 1, 'K': 2, 'L': 3, 'M': 4,
        'N': 5, 'P': 7, 'Q': 8, 'R': 9, 'S': 1,
        'T': 2, 'V': 4, 'W': 5, 'X': 6, 'Y': 7,
        'Z': 8
    }
    
    total = 0
    for char in name.upper():
        if char.isalpha() and char not in vowels:
            total += letter_values.get(char, 0)
    
    return reduce_to_single_digit(total)

def maturity(life_path_num: int, expression_num: int) -> int:
    """Calculate Maturity number (Life Path + Expression)"""
    return reduce_to_single_digit(life_path_num + expression_num)

def birthday_number(dob: str) -> int:
    """Extract birthday number from date of birth"""
    try:
        if '/' in dob:
            parts = dob.split('/')
            day = int(parts[1] if len(parts[2]) == 4 else parts[0])
        elif '-' in dob:
            day = int(dob.split('-')[2])
        else:
            day = 1
        
        return reduce_to_single_digit(day)
    except:
        return 1

# Base interpretations (PRESERVED - Core Knowledge Base)
def interpret(number: int) -> str:
    """
    Base interpretations for numerology numbers
    These are the foundational meanings - AI will enhance them
    """
    interpretations = {
        1: "Leadership, independence, innovation. You're a natural pioneer and self-starter with strong willpower.",
        2: "Cooperation, harmony, sensitivity. You excel at diplomacy and creating peaceful environments.",
        3: "Creativity, self-expression, joy. You're naturally artistic and bring optimism to others.",
        4: "Stability, hard work, practicality. You build strong foundations and value security.",
        5: "Freedom, adventure, versatility. You thrive on change and new experiences.",
        6: "Responsibility, nurturing, harmony. You're a natural caretaker focused on family and community.",
        7: "Spirituality, analysis, wisdom. You seek deeper truths and inner knowledge.",
        8: "Ambition, power, material success. You're driven to achieve and manifest abundance.",
        9: "Compassion, humanitarianism, completion. You're focused on serving others and global consciousness.",
        11: "Master Number - Intuition, inspiration, enlightenment. You have heightened spiritual awareness.",
        22: "Master Number - Master builder, manifesting dreams into reality. You can achieve great things.",
        33: "Master Number - Master teacher, spiritual healing. You uplift humanity through compassionate service."
    }
    return interpretations.get(number, "A unique path of personal growth and discovery.")

# AI Enhancement Function (WITH FALLBACK)
def enhance_with_openai(name: str, dob: str, num_type: str, number: int, base_meaning: str) -> str:
    """
    Enhance numerology reading with AI-generated personalized insights
    Uses LLM Gateway with automatic fallback (OpenAI → Groq → Base meaning)
    """
    
    async def _enhance():
        prompt = f"""Provide a personalized {num_type} number {number} reading for {name} (born {dob}).

Base interpretation: {base_meaning}

Create a warm, insightful, and encouraging reading (3-4 sentences) that:
1. Expands on the base meaning with specific, personal details
2. Relates to their life journey and potential
3. Offers actionable guidance or reflection points
4. Maintains an uplifting and empowering tone

Focus on making it feel uniquely tailored to them, not generic."""
        
        messages = [
            {
                "role": "system", 
                "content": "You are a wise and compassionate numerology expert who provides meaningful, personalized insights that resonate deeply with individuals. Your readings blend ancient wisdom with modern understanding."
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
                max_tokens=400,
                module_type="numerology",
                use_tools=False
            )
            
            if result["success"]:
                enhanced_reading = result["content"]
                # Add subtle indicator of which provider was used (optional)
                # You can remove this if you don't want to show it
                # provider_note = ""
                # if result["provider"] == "groq":
                #     provider_note = " [Enhanced via Groq AI]"
                # elif result["provider"] == "openai":
                #     provider_note = " [Enhanced via OpenAI]"
                
                return enhanced_reading
            else:
                # AI failed - return base meaning
                print(f" AI enhancement failed for {num_type}: {result.get('error')}")
                return base_meaning
                
        except Exception as e:
            print(f"Error in numerology enhancement: {e}")
            return base_meaning
    
    # Run async function synchronously
    try:
        return asyncio.run(_enhance())
    except Exception as e:
        print(f"Critical error enhancing numerology: {e}")
        return base_meaning


# Additional calculation functions (PRESERVED)
def get_personal_year(dob: str, current_year: int = None) -> int:
    """Calculate Personal Year number for current or specified year"""
    if current_year is None:
        current_year = datetime.now().year
    
    try:
        if '/' in dob:
            parts = dob.split('/')
            month = int(parts[0])
            day = int(parts[1] if len(parts[2]) == 4 else parts[0])
        elif '-' in dob:
            parts = dob.split('-')
            month = int(parts[1])
            day = int(parts[2])
        else:
            return 1
        
        total = month + day + current_year
        return reduce_to_single_digit(total)
    except:
        return 1

def get_life_path_compatibility(num1: int, num2: int) -> dict:
    """
    Calculate compatibility between two life path numbers
    Returns compatibility score and description
    """
    # Compatibility matrix (simplified)
    highly_compatible = [
        (1, 5), (1, 9), (2, 6), (2, 8), (3, 5), (3, 9),
        (4, 8), (5, 7), (6, 9), (7, 9)
    ]
    
    compatible = [
        (1, 2), (1, 3), (2, 4), (3, 6), (4, 6), (5, 9)
    ]
    
    pair = tuple(sorted([num1, num2]))
    
    if pair in highly_compatible:
        return {
            "score": 90,
            "description": "Highly compatible - natural harmony and mutual understanding"
        }
    elif pair in compatible:
        return {
            "score": 75,
            "description": "Compatible - good potential with some effort"
        }
    elif num1 == num2:
        return {
            "score": 80,
            "description": "Same path - deep understanding but potential for conflict"
        }
    else:
        return {
            "score": 60,
            "description": "Challenging - requires compromise and understanding"
        }
