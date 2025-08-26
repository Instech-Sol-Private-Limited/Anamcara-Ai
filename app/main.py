
from fastapi import FastAPI
from app.routers import tarot, dream, horoscope, numerology, summary
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routers.persona_routes import router as PersonaRouter
from app.routers.chat_routes import router as ChatRouter
from app.routers.matchmaking_routes import router as MatchRouter
from database.mongodb import close_db, connect_db
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

@app.on_event("startup")
async def startup():
    await connect_db()

    scheduler.start()

@app.on_event("shutdown")
async def shutdown():
    await close_db()
    scheduler.shutdown()

@app.get("/")
async def root():
    return {"message": "DESTINY AI SoulMate API is running", "status": "healthy"}
