
from fastapi import FastAPI
from app.routers import tarot, dream, horoscope, numerology, summary
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()
from app.routers.persona_routes import router as PersonaRouter
from app.routers.chat_routes import router as ChatRouter
from app.routers.matchmaking_routes import router as MatchRouter
from database.supabase_db import close_db, connect_db
from app.routers.scheduler import router as SchedulerRouter
from scheduler_instance import scheduler
import logging
from app.routers.ai_recommendation import router as AIRecommendationRouter
from app.routers.athena_routes import router as AthenaRouter
from app.services.llm_gateway import llm_gateway
from datetime import datetime
from app.routers.server import router as Pageredirect


app = FastAPI(title="DIVINE AI - Spiritual Guide/AI SoulMate- Athena MCQ's")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tarot.router)
app.include_router(dream.router)
app.include_router(horoscope.router)
app.include_router(numerology.router)
app.include_router(summary.router)
app.include_router(PersonaRouter, prefix="/api/persona")
app.include_router(ChatRouter, prefix="/api/chat")
app.include_router(MatchRouter, prefix="/api/match")
app.include_router(SchedulerRouter, prefix="/api/scheduler")
app.include_router(AthenaRouter, prefix="/api/athena")
app.include_router(AIRecommendationRouter, prefix="/api/ai_recommendation")
app.include_router(Pageredirect, prefix="/recommendation" )
@app.on_event("startup")
async def startup():
    """Initialize database, scheduler, and LLM Gateway on startup"""
    try:
        print("=" * 70)
        print(" STARTING DIVINE AI SOULMATE API")
        print("=" * 70)
        
        # Initialize Supabase client
        connect_db()
        print(" Supabase client initialized")
        
        # Initialize LLM Gateway (singleton - already initialized on import)
        metrics = llm_gateway.get_metrics()
        print(" LLM Gateway initialized")
        print(f"    Providers: OpenAI (primary) → Groq (fallback)")
        print(f"    Initial metrics: {metrics['total_requests']} requests")
        
        # Start the scheduler
        scheduler.start()
        print(" Scheduler started")
        
        print("=" * 70)
        print(" DIVINE AI SOULMATE API STARTED SUCCESSFULLY!")
        print("=" * 70)
        print(f" Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("")
        print(" Available endpoints:")
        print("   • Tarot Readings: /tarot/*")
        print("   • Dream Analysis: /dream/*")
        print("   • Horoscope: /horoscope/*")
        print("   • Numerology: /numerology/*")
        print("   • AI Chat: /api/chat/*")
        print("   • Matchmaking: /api/match/*")
        print("   • MCQ Tests: /api/athena/*")
        print("   • AI Metrics: /ai-metrics")
        print("   • AI Health: /ai-health")
        print("   • System Health: /health")
        print("=" * 70)
        
    except Exception as e:
        print(f" Error during startup: {e}")
        raise

@app.on_event("shutdown")
async def shutdown():
    """Clean up resources on shutdown"""
    try:
        print("\n" + "=" * 70)
        print(" SHUTTING DOWN DIVINE AI SOULMATE API")
        print("=" * 70)
        
        # Close database connection
        close_db()
        print(" Database connection closed")
        
        # Shutdown scheduler
        scheduler.shutdown()
        print(" Scheduler shut down")
        
        # Print final metrics
        metrics = llm_gateway.get_metrics()
        print("\n FINAL LLM GATEWAY STATISTICS")
        print("=" * 70)
        print(f"   Total Requests: {metrics['total_requests']}")
        print(f"   Successful: {metrics['successful_requests']}")
        print(f"   Success Rate: {metrics['success_rate']}")
        print(f"   Fallback Used: {metrics['fallback_used']} times")
        print(f"   Provider Usage: {metrics['provider_usage']}")
        print("=" * 70)
        
        print(f"\n Shut down at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(" DIVINE AI SOULMATE API SHUT DOWN GRACEFULLY")
        print("=" * 70)
        
    except Exception as e:
        print(f" Error during shutdown: {e}")

@app.get("/health")
async def health_check():
    """Detailed health check endpoint"""
    try:
        from database.supabase_db import get_client
        
        # Test database connection
        client = get_client()
        result = client.table("personas").select("count", count="exact").limit(1).execute()
        
        # Test scheduler
        scheduler_status = "running" if scheduler.running else "stopped"
        job_count = len(scheduler.get_jobs())
        
        # Get LLM metrics
        llm_metrics = llm_gateway.get_metrics()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": {
                    "status": "connected",
                    "type": "Supabase"
                },
                "scheduler": {
                    "status": scheduler_status,
                    "job_count": job_count
                },
                "llm_gateway": {
                    "status": "operational",
                    "providers": ["OpenAI", "Groq"],
                    "metrics": llm_metrics
                }
            },
            "version": "2.0.0"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": {"status": "error"},
                "scheduler": {"status": "unknown"},
                "llm_gateway": {"status": "unknown"}
            }
        }

@app.get("/")
async def root():
    return {"message": "DESTINY AI SoulMate API is running", "status": "healthy"}
