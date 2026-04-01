
from openai import AsyncOpenAI
from utils.prompt_generation import generate_personality_prompt
import os
import httpx
from app.services.llm_gateway import llm_gateway

async def generate_chat_response(messages, persona):
    """
    Generate chat response with three-tier fallback:
    TIER 1: OpenAI (via llm_gateway)
    TIER 2: Groq (via llm_gateway)
    TIER 3: Local Llama3 server (Ollama)
    """
    
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
    
    # ========================================================================
    # TIER 1 & 2: Try OpenAI → Groq (via llm_gateway)
    # ========================================================================
    result = await llm_gateway.chat_completion(
        messages=full_messages,
        temperature=0.1,
        max_tokens=500,
        module_type="simple_chat",
        use_tools=False
    )
    
    if result["success"]:
        return result["content"]
    
    # ========================================================================
    # TIER 3: Fallback to Local Llama3 Server (Your GPU)
    # ========================================================================
    try:
        print(f" TIER 3: Falling back to local Llama3 server for persona chat...")
        
        # Build Llama 3.2 native chat format
        formatted_prompt = f"<|system|>\n{system_prompt}<|end|>\n"
        
        # Convert messages to Llama format
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                formatted_prompt += f"<|user|>\n{content}<|end|>\n"
            elif role == "assistant":
                formatted_prompt += f"<|assistant|>\n{content}<|end|>\n"
        
        # Add final assistant tag
        formatted_prompt += "<|assistant|>"
        
        # Call your local Ollama server
        ollama_url = os.getenv("OLLAMA_URL", "http://192.168.18.61:11434/api/generate")
        model_name = os.getenv("OLLAMA_MODEL", "llama3.2")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                ollama_url,
                json={
                    "model": model_name,
                    "prompt": formatted_prompt,
                    "stream": False,
                    "options": {
                        "num_predict": 500,
                        "temperature": 0.1,
                    }
                },
            )
            resp.raise_for_status()
            data = resp.json()
            response_text = data.get("response", "").strip()
            
            if response_text:
                print(f" TIER 3 SUCCESS: Local Llama3 generated response")
                return response_text
            else:
                raise Exception("Empty response from Ollama")
                
    except Exception as e:
        print(f" TIER 3 FAILED: {str(e)}")
        # Final fallback message
        return "I'm having trouble connecting right now. Could you try again in a moment?"
    
