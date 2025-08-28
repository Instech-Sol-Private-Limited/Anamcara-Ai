# routes/matchmaking_routes.py
from fastapi import APIRouter, HTTPException
from models.schemas import UserFormData
from models.supabase_helpers import serialize_doc, convert_form_data_to_arrays
from database.supabase_db import get_client
import json
router = APIRouter()
from fastapi import Request

@router.post("/form")
async def submit_user_form(request: Request, data: UserFormData):
    try:
        # Option A: Use the validated data object (easier)
        print(f"User ID: {data.user_id}")
        print(f"Kind connection: {data.kind_connection}")
        
        # Option B: If you need raw body for debugging
        body = await request.body()
        print(f"Raw body length: {len(body)}")
        
        # Use the validated data
        client = get_client()
        form_data = data.dict()
        
        existing_result = client.table("user_forms").select("*").eq("user_id", data.user_id).execute()
        
        if existing_result.data:
            result = client.table("user_forms").update(form_data).eq("user_id", data.user_id).execute()
            return {"message": "Form data updated successfully"}
        else:
            result = client.table("user_forms").insert(form_data).execute()
            return {"message": "Form data submitted successfully"}
            
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/find/{user_id}")
async def find_match(user_id: str):
    try:
        client = get_client()
        
        # Get user's form data
        user_result = client.table("user_forms").select("*").eq("user_id", user_id).execute()
        
        if not user_result.data:
            raise HTTPException(status_code=404, detail="User form data not found")
        
        user_data = user_result.data[0]
        
        # Get all other users' form data
        others_result = client.table("user_forms").select("*").neq("user_id", user_id).execute()
        
        if not others_result.data:
            return {"message": "No other users found for matching"}
        
        matches = []
        user_fields = [
            "kind_connection", "social_energy_feel_most", "favorite_conversations_light_up", 
            "happiest_hobbies", "top_must_haves_to_match_you", "deal_breakers", 
            "self_words", "click_best_with", "care_language", "conflict_style_handle", 
            "non_negotiable_friend"
        ]
        
        for other_user in others_result.data:
            total_fields = len(user_fields)
            matching_score = 0
            
            for field in user_fields:
                user_values = user_data.get(field, [])
                other_values = other_user.get(field, [])
                
                if isinstance(user_values, list) and isinstance(other_values, list):
                    # Convert lists to sets for intersection
                    user_set = set()
                    other_set = set()
                    
                    # Handle comma-separated values within list items
                    for item in user_values:
                        if isinstance(item, str):
                            user_set.update([i.strip() for i in item.split(",")])
                        else:
                            user_set.add(str(item))
                    
                    for item in other_values:
                        if isinstance(item, str):
                            other_set.update([i.strip() for i in item.split(",")])
                        else:
                            other_set.add(str(item))
                    
                    # Check for common elements
                    if user_set & other_set:
                        matching_score += 1
                else:
                    # Direct comparison for non-list values
                    if user_values == other_values and user_values is not None:
                        matching_score += 1
            
            # Calculate match percentage
            match_percentage = (matching_score / total_fields) * 100
            
            # Only include matches with 70% or higher compatibility
            if match_percentage >= 70:
                matches.append({
                    "match_id": other_user["user_id"],
                    "name": other_user.get("name", "Unknown"),
                    "percent_match": round(match_percentage, 1),
                    "data": serialize_doc(other_user)
                })
        
        # Sort matches by percentage (highest first)
        matches.sort(key=lambda x: x["percent_match"], reverse=True)
        
        if matches:
            return {"matches": matches}
        else:
            return {"message": "No matches found with 70% or higher compatibility"}
            
    except Exception as e:
        print(f"Error finding matches: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to find matches: {str(e)}")

@router.get("/form/{user_id}")
async def get_user_form(user_id: str):
    try:
        client = get_client()
        
        result = client.table("user_forms").select("*").eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="User form data not found")
        
        return serialize_doc(result.data[0])
        
    except Exception as e:
        print(f"Error getting user form: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user form: {str(e)}")

@router.delete("/form/{user_id}")
async def delete_user_form(user_id: str):
    try:
        client = get_client()
        
        result = client.table("user_forms").delete().eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="User form data not found")
        
        return {"message": "User form data deleted successfully"}
        
    except Exception as e:
        print(f"Error deleting user form: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete user form: {str(e)}")