
from fastapi import FastAPI
from app.routers import tarot, dream, horoscope, numerology, summary
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="DIVINE AI - Spiritual Guide")
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
