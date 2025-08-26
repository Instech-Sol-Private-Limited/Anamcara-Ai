from fastapi import APIRouter, HTTPException
from models.schemas import UserFormData

router = APIRouter()

@router.post("/form")
async def submit_user_form(data: UserFormData):
    from database.mongodb import db  # <-- import inside the function
    await db.users.insert_one(data.dict())
    return {"message": "Form data submitted"}

from bson import ObjectId

def serialize_doc(doc):
    doc = dict(doc)
    if "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc

@router.get("/find/{user_id}")
async def find_match(user_id: str):
    from database.mongodb import db
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    cursor = db.users.find({"user_id": {"$ne": user_id}})
    matches = []
    user_fields = [
        "kind_connection", "social_energy_feel_most", "favorite_conversations_light_up", "happiest_hobbies",
        "top_must_haves_to_match_you", "deal_breakers", "self_words", "click_best_with",
        "care_language", "conflict_style_handle", "non_negotiable_friend"
    ]

    async for other in cursor:
        total = len(user_fields)
        score = 0
        for field in user_fields:
            u_val = user.get(field)
            o_val = other.get(field)
            if isinstance(u_val, list) and isinstance(o_val, list):
                u_items = set()
                for item in u_val:
                    u_items.update([i.strip() for i in item.split(",")])
                o_items = set()
                for item in o_val:
                    o_items.update([i.strip() for i in item.split(",")])
                if u_items & o_items:
                    score += 1
            else:
                if u_val == o_val and u_val is not None:
                    score += 1
        percent = (score / total) * 100
        if percent >= 70:
            matches.append({
                "match_id": other["user_id"],
                "name": other.get("name", ""),
                "percent_match": percent,
                "data": serialize_doc(other)
            })

    if matches:
        return {"matches": matches}
    else:
        return {"message": "No matches found"}