# # app/routers/numerology.py

# from fastapi import APIRouter
# from app.services.numerology_service import life_path, expression, soul_urge, interpret

# router = APIRouter(prefix="/numerology", tags=["Numerology"])

# @router.get("/")
# def numerology(name: str, dob: str):
#     lp = life_path(dob)
#     exp = expression(name)
#     soul = soul_urge(name)
#     return {
#         "LifePath": {"number": lp, "meaning": interpret(lp)},
#         "Expression": {"number": exp, "meaning": interpret(exp)},
#         "SoulUrge": {"number": soul, "meaning": interpret(soul)}
#     }

# app/routers/numerology.py
from fastapi import APIRouter
from app.services.numerology_service import (
    life_path, expression, soul_urge,
    interpret, enhance_with_openai
)

router = APIRouter(prefix="/numerology", tags=["Numerology"])

# ----- BASIC NUMEROLOGY -----
@router.get("/")
def numerology(name: str, dob: str):
    lp_num = life_path(dob)
    exp_num = expression(name)
    soul_num = soul_urge(name)

    return {
        "LifePath": {"number": lp_num, "meaning": interpret(lp_num)},
        "Expression": {"number": exp_num, "meaning": interpret(exp_num)},
        "SoulUrge": {"number": soul_num, "meaning": interpret(soul_num)}
    }


# ----- ENHANCED NUMEROLOGY -----
@router.get("/enhanced")
def numerology_enhanced(name: str, dob: str):
    lp_num = life_path(dob)
    exp_num = expression(name)
    soul_num = soul_urge(name)

    lp_base = interpret(lp_num)
    exp_base = interpret(exp_num)
    soul_base = interpret(soul_num)

    return {
        "LifePath": {
            "number": lp_num,
            "meaning": lp_base,
            "enhanced_reading": enhance_with_openai(name, dob, "Life Path", lp_num, lp_base)
        },
        "Expression": {
            "number": exp_num,
            "meaning": exp_base,
            "enhanced_reading": enhance_with_openai(name, dob, "Expression", exp_num, exp_base)
        },
        "SoulUrge": {
            "number": soul_num,
            "meaning": soul_base,
            "enhanced_reading": enhance_with_openai(name, dob, "Soul Urge", soul_num, soul_base)
        }
    }
