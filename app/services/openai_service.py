
from openai import AsyncOpenAI
from utils.prompt_generation import generate_personality_prompt
import os
from app.services.llm_gateway import llm_gateway

async def generate_chat_response(messages, persona):
    """Generate chat response using LLM Gateway with fallback"""
    
    # Build system prompt from persona
    personality_traits = persona.get('personality_traits', [])
    if isinstance(personality_traits, str):
        personality_traits = [personality_traits]
    
    system_prompt = f"""You are {persona['name']}, a {persona['gender']} AI companion with these traits: {', '.join(personality_traits)}.
Be warm, empathetic, and engage naturally in conversation. Respond as this persona would."""
    
    full_messages = [
        {"role": "system", "content": system_prompt},
        *messages
    ]
    
    result = await llm_gateway.chat_completion(
        messages=full_messages,
        temperature=0.4,
        max_tokens=500,
        module_type="simple_chat",
        use_tools=False
    )
    
    if result["success"]:
        return result["content"]
    else:
        # Fallback message
        return "I'm having trouble connecting right now. Could you try again in a moment?"