
from fastapi import FastAPI
from app.routers import tarot, dream, horoscope, numerology, summary
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routers.persona_routes import router as PersonaRouter
from app.routers.chat_routes import router as ChatRouter
from app.routers.matchmaking_routes import router as MatchRouter
from database.supabase_db import close_db, connect_db
from app.routers.scheduler import router as SchedulerRouter
from scheduler_instance import scheduler
import logging

load_dotenv()
app = FastAPI(title="DIVINE AI - Spiritual Guide/AI SoulMate")
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


@app.on_event("startup")
async def startup():
    """Initialize database and scheduler on startup"""
    try:
        # Initialize Supabase client
        connect_db()
        print("✅ Supabase client initialized")
        
        # Start the scheduler
        scheduler.start()
        print("✅ Scheduler started")
        
        print("🚀 DESTINY AI SoulMate API started successfully!")
        
    except Exception as e:
        print(f"❌ Error during startup: {e}")
        raise

@app.on_event("shutdown")
async def shutdown():
    """Clean up resources on shutdown"""
    try:
        # Close database connection
        close_db()
        print("✅ Database connection closed")
        
        # Shutdown scheduler
        scheduler.shutdown()
        print("✅ Scheduler shut down")
        
        print("👋 DESTINY AI SoulMate API shut down gracefully")
        
    except Exception as e:
        print(f"❌ Error during shutdown: {e}")

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
        
        return {
            "status": "healthy",
            "database": {
                "status": "connected",
                "type": "Supabase"
            },
            "scheduler": {
                "status": scheduler_status,
                "job_count": job_count
            },
            "timestamp": "2025-01-01T00:00:00Z"  # This would be actual timestamp
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "database": {
                "status": "error",
                "type": "Supabase"
            },
            "scheduler": {
                "status": "unknown",
                "job_count": 0
            }
        }

@app.get("/")
async def root():
    return {"message": "DESTINY AI SoulMate API is running", "status": "healthy"}
