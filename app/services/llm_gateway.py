import os
import asyncio
from typing import Optional, List, Dict
from enum import Enum
from openai import AsyncOpenAI
from groq import AsyncGroq
from datetime import datetime
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelProvider(Enum):
    OPENAI = "openai"
    GROQ = "groq"

class LLMGateway:
    """Centralized LLM Gateway with automatic fallback"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMGateway, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
            
            self.providers = {
                "openai": {
                    "client": self.openai_client,
                    "model": "gpt-4o",
                    "timeout": 30
                },
                "groq": {
                    "client": self.groq_client,
                    "model": "llama-3.3-70b-versatile",
                    "timeout": 30
                }
            }
            
            self.metrics = {
                "total_requests": 0,
                "successful_requests": 0,
                "fallback_used": 0,
                "provider_usage": {}
            }
            
            self.initialized = True
            logger.info(" LLM Gateway initialized with OpenAI + Groq fallback")
    
    async def chat_completion(
        self,
        messages: List[Dict],
        temperature: float = 0.4,
        max_tokens: int = 2000,
        model: Optional[str] = None,
        module_type: str = "simple_chat",
        use_tools: bool = False
    ) -> Dict:
        """
        Get chat completion with automatic fallback
        
        Args:
            messages: List of chat messages
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            model: Override default model
            module_type: Type of task (for fallback strategy)
            use_tools: Whether this needs function calling (disables Groq)
        
        Returns:
            {
                "success": True/False,
                "content": "AI response",
                "provider": "openai"/"groq",
                "fallback_used": bool,
                "error": None or error message
            }
        """
        self.metrics["total_requests"] += 1
        
        # Determine which providers to try based on task type
        if use_tools or module_type == "mcq_generation_agent":
            providers_to_try = ["openai"]  # Only OpenAI supports agents/tools
        else:
            providers_to_try = ["openai", "groq"]  # Both work for simple tasks
        
        for idx, provider_name in enumerate(providers_to_try):
            provider_config = self.providers[provider_name]
            client = provider_config["client"]
            model_name = model or provider_config["model"]
            timeout = provider_config["timeout"]
            
            try:
                logger.info(f" Attempting {provider_name} ({model_name})...")
                
                response = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens
                    ),
                    timeout=timeout
                )
                
                content = response.choices[0].message.content
                
                # Success!
                self.metrics["successful_requests"] += 1
                self.metrics["provider_usage"][provider_name] = \
                    self.metrics["provider_usage"].get(provider_name, 0) + 1
                
                if idx > 0:  # Used fallback
                    self.metrics["fallback_used"] += 1
                
                logger.info(f" Success with {provider_name}")
                
                return {
                    "success": True,
                    "content": content,
                    "provider": provider_name,
                    "fallback_used": idx > 0,
                    "error": None
                }
                
            except asyncio.TimeoutError:
                logger.warning(f"⏱ {provider_name} timeout after {timeout}s")
                continue
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f" {provider_name} error: {error_msg}")
                
                # Check if it's a quota/credit error
                if any(x in error_msg.lower() for x in ["quota", "insufficient", "429", "rate_limit", "rate limit"]):
                    logger.warning(f"💳 {provider_name} quota exceeded, trying fallback...")
                    continue
                
                # For other errors, continue to fallback
                continue
        
        # All providers failed
        logger.error(" ALL PROVIDERS FAILED")
        return {
            "success": False,
            "content": self._get_fallback_message(module_type),
            "provider": "none",
            "fallback_used": True,
            "error": "All AI providers unavailable"
        }
    
    def _get_fallback_message(self, module_type: str) -> str:
        """Return appropriate fallback message based on module"""
        fallback_messages = {
            "mcq_generation": "Unable to generate test questions at this time. Please try again shortly or contact support.",
            "mcq_generation_agent": "Unable to generate test questions at this time. Please try again shortly.",
            "simple_chat": "I'm having trouble connecting right now. Could you try again in a moment?",
            "tarot_reading": "The cosmic energies are a bit clouded right now. Please try your reading again.",
            "numerology": "Unable to calculate your numerology reading at this time.",
            "dream_analysis": "Dream analysis temporarily unavailable. Please try again shortly."
        }
        return fallback_messages.get(module_type, "Service temporarily unavailable. Please try again.")
    
    def get_metrics(self) -> Dict:
        """Get usage statistics"""
        success_rate = (self.metrics["successful_requests"] / 
                       self.metrics["total_requests"] * 100 
                       if self.metrics["total_requests"] > 0 else 0)
        
        return {
            "total_requests": self.metrics["total_requests"],
            "successful_requests": self.metrics["successful_requests"],
            "success_rate": f"{success_rate:.2f}%",
            "fallback_used": self.metrics["fallback_used"],
            "provider_usage": self.metrics["provider_usage"]
        }

# Singleton instance
llm_gateway = LLMGateway()