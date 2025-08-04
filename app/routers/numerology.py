# app/routers/numerology.py

from fastapi import APIRouter
from app.services.numerology_service import life_path, expression, soul_urge, interpret

router = APIRouter(prefix="/numerology", tags=["Numerology"])

@router.get("/")
def numerology(name: str, dob: str):
    lp = life_path(dob)
    exp = expression(name)
    soul = soul_urge(name)
    return {
        "LifePath": {"number": lp, "meaning": interpret(lp)},
        "Expression": {"number": exp, "meaning": interpret(exp)},
        "SoulUrge": {"number": soul, "meaning": interpret(soul)}
    }
