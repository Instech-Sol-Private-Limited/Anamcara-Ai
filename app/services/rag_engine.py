import chromadb
from sentence_transformers import SentenceTransformer
import httpx
import asyncio
import os
import json

# -------------------------
# Load embedder
# -------------------------
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# -------------------------
# Load ChromaDB
# -------------------------
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
chroma_path = os.path.join(base_dir, "chroma_db")
print(f"Loading ChromaDB from: {chroma_path}")  # Add this debug line
os.makedirs(chroma_path, exist_ok=True)

client = chromadb.PersistentClient(path=chroma_path)
collection = None  # Initialize as None

def get_collection():
    """Get or create collection"""
    global collection
    if collection is None:
        try:
            collection = client.get_collection("anamcore_pdf")
        except chromadb.errors.NotFoundError:
            collection = client.create_collection("anamcore_pdf")
    return collection

# -------------------------
# URL mapping (moved to separate dict for easier maintenance)
# -------------------------
URL_MAP = {
    "soulfeed": {
        "url": "https://anamcara.ai/soulfeed",
        "keywords": [
            "feed", "timeline", "scroll", "posts", "updates", "social", "discover",
            "content feed", "daily posts", "stories", "explore"
        ]
    },
    "nirvana": {
        "url": "https://anamcara.ai/nirvana",
        "keywords": [
            "threads", "discussions", "community", "public talk", "forum",
            "conversation board", "opinions", "group topics", "debates"
        ]
    },
    "chambers": {
        "url": "https://anamcara.ai/chambers",
        "keywords": [
            "private chat", "private rooms", "confidential", "1-on-1",
            "secure space", "intimate conversation", "safe room", "private zone"
        ]
    },
    "soulvibe": {
        "url": "https://anamcara.ai/soulvibe",
        "keywords": [
            "vibe", "random chat", "connect", "meet people", "chat rooms",
            "social vibe", "talk to strangers", "new people", "live chat",
            "matching", "quick chat"
        ]
    },
    "soulstream": {
        "url": "https://anamcara.ai/soulstream",
        "keywords": [
            "live stream", "broadcast", "go live", "streaming", "live content",
            "stream", "creator live", "real time", "live sessions"
        ]
    },
    "soulplay": {
        "url": "https://anamcara.ai/soulplay",
        "keywords": [
            "videos", "entertainment", "clips", "watch content", "short videos",
            "funny videos", "viral", "creative videos"
        ]
    },
    "soulstories": {
        "url": "https://anamcara.ai/soulstories",
        "keywords": [
            "stories", "write", "fiction", "creative writing", "short stories",
            "poetry", "novels", "manga", "webtoon", "books", "literature",
            "story creation"
        ]
    },
    "soulacademy": {
        "url": "https://anamcara.ai/soulacademy",
        "keywords": [
            "learn", "education", "courses", "training", "skills",
            "tutorials", "knowledge", "lessons", "study", "learning modules"
        ]
    },
    "soulconnect": {
        "url": "https://anamcara.ai/soulconnect",
        "keywords": [
            "hire", "services", "marketplace", "freelance", "consulting",
            "tutoring", "booking", "professional", "experts", "help", "mentors"
        ]
    },
    "startup": {
        "url": "https://anamcara.ai/startup",
        "keywords": [
            "startup", "business", "entrepreneurship", "earning", "work",
            "career", "projects", "grow business", "ideas", "build startup"
        ]
    },
    "hope": {
        "url": "https://anamcara.ai/hope",
        "keywords": [
            "crisis", "help", "mental support", "emotional support", "emergency",
            "grounding", "comfort", "distress support", "safety", "calm"
        ]
    },
    "shop": {
        "url": "https://anamcara.ai/shop",
        "keywords": [
            "shop", "buy", "products", "store", "purchase",
            "items", "market", "shopping", "anamcara shop"
        ]
    },
    "vault": {
        "url": "https://anamcara.ai/vault",
        "keywords": [
            "vault", "save", "storage", "privacy", "secure", "protected",
            "my data", "saved items"
        ]
    },
    "leaderboard": {
        "url": "https://anamcara.ai/leaderboard",
        "keywords": [
            "leaderboard", "ranking", "top users", "scores", "achievements",
            "performance", "top creators"
        ]
    },
    "anamgurus": {
        "url": "https://anamcara.ai/anamgurus",
        "keywords": [
            "ai assistant", "gurus", "anamguru", "ai guide",
            "chatbot", "personal guide", "coaches"
        ]
    },
    "destiny": {
        "url": "https://anamcara.ai/anamgurus/destiny",
        "keywords": [
            "dating", "love", "romance", "relationship", "partner",
            "soulmate", "matchmaking", "compatibility", "connection"
        ]
    },
    "divine": {
        "url": "https://anamcara.ai/anamgurus/divine",
        "keywords": [
            "tarot", "numerology", "horoscope", "spiritual", "dreams",
            "astrology", "guidance", "cosmic", "fortune", "interpretation"
        ]
    },
    "lokaris": {
        "url": "https://anamcara.ai/anamgurus/lokaris",
        "keywords": [
            "games", "play", "fun", "gaming", "mini games",
            "challenges", "arcade", "puzzles", "chess"
        ]
    },
    "athena": {
        "url": "https://anamcara.ai/anamgurus/athena",
        "keywords": [
            "knowledge", "education", "learning", "facts", "study aid",
            "academic help", "explanations", "teaching", "understanding"
        ]
    },
    "oasis": {
        "url": "https://anamcara.ai/oasis",
        "keywords": [
            "rewards", "earning", "performance", "analytics",
            "user stats", "progress", "activity rewards", "engagement"
        ]
    },
    "chess": {
        "url": "https://anamcara.ai/chess",
        "keywords": [
            "chess", "play chess", "game strategy", "board game",
            "match chess", "practice chess"
        ]
    },
    "help": {
        "url": "https://anamcara.ai/help-and-policy",
        "keywords": [
            "help", "support", "policy", "faq", "issues",
            "questions", "guide", "contact"
        ]
    }
}


# -------------------------
# Retrieve relevant chunks (optimized)
# -------------------------
def _retrieve_chunks_sync(query, top_k=3):
    coll = get_collection()
    count = coll.count()
    print(f"Collection has {count} documents")
    if count == 0:  # ← ADD THIS
        print("No documents in collection, returning empty list")
        return []
    
    results = coll.query(
        query_texts=[query],  # Changed from query_embeddings
        n_results=min(top_k, count),
    )
    
    docs = results["documents"][0] if results["documents"] else []
    print(f"Retrieved {len(docs)} chunks: {[d[:50] for d in docs]}")
    return docs

async def retrieve_chunks(query, top_k=3):
    return await asyncio.to_thread(_retrieve_chunks_sync, query, top_k)


# -------------------------
# Async Ask Ollama with streaming support
# -------------------------
_OLLAMA_SEMAPHORE = asyncio.Semaphore(3)  # Increased from 2 to 3


async def ask_ollama_stream(model, prompt, timeout_seconds: int = 60):
    """
    Async streaming call to Ollama API - yields text chunks as they arrive
    """
    url = "https://anamcara.ai/llama/api/generate"
    
    async with _OLLAMA_SEMAPHORE:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            try:
                async with client.stream(
                    "POST",
                    url,
                    json={"model": model, "prompt": prompt, "stream": True},
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if line.strip():
                            try:
                                chunk = json.loads(line)
                                if "response" in chunk:
                                    yield chunk["response"]
                            except json.JSONDecodeError:
                                continue
            except httpx.ConnectError:
                yield "Error: Ollama server is not running."
            except httpx.ReadTimeout:
                yield "Error: Request timed out."
            except Exception as e:
                yield f"Error: {str(e)}"


async def ask_ollama(model, prompt, timeout_seconds: int = 180, max_attempts: int = 2):
    """
    Non-streaming version - collects full response
    Reduced timeout from 180s to 60s and attempts from 3 to 2
    """
    url = "https://anamcara.ai/llama/api/generate"
    backoff_base = 1

    async with _OLLAMA_SEMAPHORE:
        async with httpx.AsyncClient() as client:
            for attempt in range(1, max_attempts + 1):
                try:
                    resp = await client.post(
                        url,
                        json={
                            "model": model,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "num_predict": 200,  # Limit response length
                                "temperature": 0.3,
                                "top_p": 0.9,
                            }
                        },
                        timeout=timeout_seconds,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    text = data.get("response", "") or ""
                    return text.strip()
                except httpx.ConnectError:
                    print(f"[attempt {attempt}] Ollama server not reachable")
                    if attempt == max_attempts:
                        return "Error: Ollama server is not running."
                except httpx.ReadTimeout:
                    print(f"[attempt {attempt}] Timeout (timeout={timeout_seconds}s)")
                except Exception as e:
                    print(f"[attempt {attempt}] Failed: {e}")

                if attempt < max_attempts:
                    sleep_for = backoff_base * (2 ** (attempt - 1))
                    print(f"Retrying in {sleep_for}s...")
                    await asyncio.sleep(sleep_for)

    return "Error: Ollama server did not respond."


async def warmup_model(model: str, timeout_seconds: int = 120):
    """Reduced warmup timeout from 300s to 120s"""
    try:
        prompt = "Hello"  # More realistic warmup
        res = await ask_ollama(model, prompt, timeout_seconds=timeout_seconds, max_attempts=1)
        print(f"✓ Model {model} warmed up")
        return res
    except Exception as e:
        print(f"✗ Warmup failed for {model}: {e}")
        return f"Error: {e}"


# -------------------------
# Extract relevant URLs based on context
# -------------------------
def extract_relevant_urls(query: str, context: str, max_urls: int = 2) -> list[dict]:
    """
    Extract relevant URLs based on keyword matching
    Returns list of dicts with 'name' and 'url'
    """
    query_lower = query.lower()
    context_lower = context.lower()
    combined = query_lower + " " + context_lower
    
    scored_urls = []
    
    for key, data in URL_MAP.items():
        score = 0
        
        # Check if any keyword matches in query (higher priority)
        for keyword in data["keywords"]:
            if keyword in query_lower:
                score += 10
        
        # Check if any keyword matches in context
        for keyword in data["keywords"]:
            if keyword in context_lower:
                score += 5
        
        # Check if module name matches
        if key in query_lower or key in context_lower:
            score += 15
        
        if score > 0:
            scored_urls.append({
                "name": key.replace("_", " ").title(),
                "url": data["url"],
                "score": score
            })
    
    # Sort by score and return top matches
    scored_urls.sort(key=lambda x: x["score"], reverse=True)
    return [{"name": u["name"], "url": u["url"]} for u in scored_urls[:max_urls]]

# -------------------------
# Optimized RAG function
# -------------------------
async def rag_query(
    user_query: str, 
    chat_history: str = "",  # NEW: Previous conversation context
    use_streaming: bool = False
):
    """
    Optimized RAG query with:
    - Shorter, focused prompt
    - Dynamic URL selection
    - Optional streaming
    """
    
    # Retrieve fewer, more relevant chunks
    docs = await retrieve_chunks(user_query, top_k=3)
    context = "\n\n".join(docs)
    print("thois is the context", context)
    # Extract only relevant URLs
    relevant_urls = extract_relevant_urls(user_query, context, max_urls=3)
    url_context = ""
    if relevant_urls:
        url_context = "\n\nRELEVANT MODULES:\n"
        for link in relevant_urls:
            url_context += f"- {link['name']}: {link['url']}\n"
    # urls_text = "\n".join(relevant_urls) if relevant_urls else ""
    print("thos os the urls", url_context)
    history_context = f"\n{chat_history}\n" if chat_history else ""
    # Shorter, more focused prompt
    prompt = f"""
You are **Desire**, the main assistant of ANAMCARA.
Never mention you are an AI model.
In response user these terms " Desire AI", " trusted AnamGuru", Not used assistant, and AI words like "trusted assistant", "Desire AI"
Analyze the user query and then if the context is needed for response, use it and if not response directly from your knowledge.
Follow these rules STRICTLY:
1. Use ONLY the context and module descriptions provided.
2. If the user's query maps to any module (via keywords or context), ALWAYS respond by:
   - Understanding user intent
   - Guiding them to the correct module
   - Giving a warm, human, supportive response  
3. If user asks about earning money → prioritize:
   - SoulConnect (freelancing, services)
   - Oasis (earn rewards)
   - Startup (business & entrepreneurship)
4. If user wants to make friends → prioritize:
   - SoulVibe (meet new people)
   - SoulFeed (social feed)
5. NEVER hallucinate URLs. ONLY use modules provided in the URL list.
6. Insert URLs using <a href=""> format (HTML anchor tag).

---

CONTEXT (shortened):
{context[:1000]}

CHAT HISTORY:
{history_context}

USER QUERY:
{user_query}

---

Based on the above, provide a short, warm, helpful answer.
If relevant, suggest modules using the correct URLs:

{url_context}

ANSWER:
"""

    if use_streaming:
        # Return async generator for streaming
        return ask_ollama_stream("llama3.2", prompt, timeout_seconds=60)
    else:
        # Return complete response
        response = await ask_ollama("llama3.2", prompt, timeout_seconds=60)
        return response


# -------------------------
# Alternative: Use smaller/faster model
# -------------------------
async def rag_query_fast(user_query: str):
    """
    Ultra-fast version using a smaller model like llama3.2:1b
    Consider using: tinyllama, llama3.2:1b, or phi3:mini
    """
    docs = await retrieve_chunks(user_query, top_k=1)  # Only 1 chunk
    context = docs[0] if docs else ""
    
    relevant_urls = extract_relevant_urls(user_query, context, max_urls=2)
    urls_text = "\n".join(relevant_urls) if relevant_urls else ""

    prompt = f"""Context: {context[:400]}

Q: {user_query}
URLs: {urls_text}

Brief answer:"""

    # Use smaller, faster model
    response = await ask_ollama("llama3.2:1b", prompt, timeout_seconds=30)
    return response

async def warmup_model(model: str, timeout_seconds: int = 300):
    """Send a short warmup request to ensure the model is loaded into Ollama runners.

    This function uses a short prompt and respects the same concurrency limits.
    It returns the raw Ollama response or an Error: message.
    """
    try:
        prompt = "__warmup__"
        # use fewer attempts for warmup
        res = await ask_ollama(model, prompt, timeout_seconds=timeout_seconds, max_attempts=2)
        print(f"Warmup result for {model}: {res[:200]}")
        return res
    except Exception as e:
        print(f"Warmup failed for {model}: {e}")
        return f"Error: {e}"


async def warmup_models(models: list[str], timeout_seconds: int = 300):
    """Warm up a list of models concurrently but constrained by the same semaphore.
    Schedule warmups sequentially to avoid overloading the server.
    """
    results = {}
    for m in models:
        results[m] = await warmup_model(m, timeout_seconds=timeout_seconds)
    return results

