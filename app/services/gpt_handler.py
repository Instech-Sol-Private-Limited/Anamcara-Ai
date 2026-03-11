import os
from dotenv import load_dotenv
from app.services.llm_gateway import llm_gateway
import asyncio
import httpx

load_dotenv()


def generate_poetic_summary(name, cards, dream_link=None):
    card_descriptions = "\n".join([f"- {card['name']} ({card['orientation']})" for card in cards])
    prompt = f"""
You are a poetic spiritual guide. Write a 3-4 line poetic summary for {name}, based on their Tarot reading.
The drawn cards are:
{card_descriptions}

Dream link (if any): {dream_link or "None"}

Respond in a poetic tone, combining mystical symbolism and emotional depth. Make it inspiring.
"""

    # Build messages for LLM gateway (OpenAI → Groq, then fallback text)
    messages = [
        {"role": "system", "content": "You are a poetic, mystical tarot interpreter."},
        {"role": "user", "content": prompt},
    ]

    # We may be called from sync context; use asyncio.run if no loop is running
    async def _run():
        # TIER 1 & 2: Try OpenAI → Groq (via llm_gateway)
        result = await llm_gateway.chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=300,
            module_type="simple_chat",
            use_tools=False,
        )
        if result.get("success"):
            return result.get("content", "")
        
        # TIER 3: Fallback to Local Llama3 Server
        print(f" TIER 3: Falling back to local Llama3 for poetic summary...")
        try:
            ollama_url = os.getenv("OLLAMA_URL", "http://192.168.18.61:11434/api/generate")
            model_name = os.getenv("OLLAMA_MODEL", "llama3.2")
            
            # Build Llama format prompt
            llama_prompt = f"<|system|>\n{messages[0]['content']}<|end|>\n<|user|>\n{messages[1]['content']}<|end|>\n<|assistant|>"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    ollama_url,
                    json={
                        "model": model_name,
                        "prompt": llama_prompt,
                        "stream": False,
                        "options": {
                            "num_predict": 300,
                            "temperature": 0.7,
                        }
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                summary = data.get("response", "").strip()
                
                if summary:
                    print(f" TIER 3 SUCCESS: Local Llama3 generated poetic summary")
                    return summary
                else:
                    raise Exception("Empty response from Ollama")
                    
        except Exception as e:
            print(f" TIER 3 FAILED: {str(e)}")
            # Final fallback message
            return "The cards are quiet right now. Please try again in a moment."

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop – safe to create one
        return asyncio.run(_run())
    else:
        # Inside an existing event loop; run as task and block until done
        return loop.run_until_complete(_run())

