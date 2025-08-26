
from openai import AsyncOpenAI
from utils.prompt_generation import generate_personality_prompt
import os

def get_openai_client():
    return AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_chat_response(messages, persona):
    """Generate chat response adapted to the specific persona"""
    client = get_openai_client()
    
    # Extract persona data
    traits = persona.get("personality_traits", [])
    name = persona.get("name", "Assistant")
    gender = persona.get("gender", "neutral")
    
    # Optional: Add more persona context if available in your database
    additional_context = persona.get("background", None) or persona.get("bio", None)
    
    # Generate adaptive system prompt
    system_prompt = generate_personality_prompt(
        traits=traits,
        name=name, 
        gender=gender,
        additional_context=additional_context
    )
    
    # Build message chain with persona context
    full_messages = [{"role": "system", "content": system_prompt}] + messages

    response = await client.chat.completions.create(
        model="gpt-4",
        messages=full_messages,
        temperature=0.2,  # Slightly higher for more personality variation
        max_tokens=150,   # Keep responses concise for chat
        presence_penalty=0.1,  # Encourage natural variation
        frequency_penalty=0.1  # Reduce repetitive responses
    )

    return response.choices[0].message.content

