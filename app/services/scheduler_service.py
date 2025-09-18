from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from app.services.openai_service import generate_chat_response
from utils.prompt_generation import generate_personality_prompt
import pytz
from scheduler_instance import scheduler
from database.supabase_db import get_client

# Mood check-in scheduler that runs every hour to check for inactive personas
async def start_mood_checkin_scheduler():
    """Start the mood check-in scheduler that runs every hour"""
    pakistan_tz = pytz.timezone('Asia/Karachi')
    
    # Schedule mood check to run every hour
    scheduler.add_job(
        check_personas_for_mood_greeting,
        CronTrigger(minute=0, timezone=pakistan_tz),  # Run at the start of every hour
        id="mood_checkin_scanner",
        replace_existing=True
    )
    print("Mood check-in scanner scheduled to run every hour")

async def check_personas_for_mood_greeting():
    """Check all personas and send mood greetings to those inactive for 12+ hours"""
    try:
        client = get_client()
        current_time = datetime.utcnow()
        twelve_hours_ago = current_time - timedelta(hours=12)
        
        print(f"Checking personas for mood greetings at {current_time}")
        
        # Get all personas with last_interaction older than 12 hours or null
        # No joins with users table - we'll check preferences separately
        personas_result = client.table("personas").select("*").or_(
            f"last_interaction.lt.{twelve_hours_ago.isoformat()},last_interaction.is.null"
        ).execute()
        
        if not personas_result.data:
            print("No personas found needing mood check-in")
            return
        
        print(f"Found {len(personas_result.data)} personas needing mood check-in")
        
        # Check each persona's user preference separately
        eligible_personas = []
        for persona in personas_result.data:
            try:
                # Check if user has mood check-ins enabled
                user_enabled = await check_user_mood_preference(persona["user_id"])
                if user_enabled:
                    eligible_personas.append(persona)
                else:
                    print(f"Skipping persona {persona.get('name', 'Unknown')} - user has disabled mood check-ins")
            except Exception as e:
                print(f"Error checking preference for persona {persona.get('id', 'unknown')}: {str(e)}")
                # Default to enabled if we can't check preference
                eligible_personas.append(persona)
        
        if not eligible_personas:
            print("No eligible personas found (all users have disabled mood check-ins)")
            return
        
        print(f"Found {len(eligible_personas)} eligible personas for mood check-in")
        
        for persona in eligible_personas:
            try:
                # Check if we already sent a mood greeting today
                today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
                
                mood_messages_today = client.table("mood_messages").select("*").eq(
                    "persona_id", persona["id"]
                ).gte("timestamp", today_start.isoformat()).execute()
                
                if mood_messages_today.data:
                    print(f"Already sent mood greeting today for persona {persona.get('name', 'Unknown')} ({persona['id']})")
                    continue
                
                await send_mood_greeting(persona)
                print(f"Sent mood greeting to {persona.get('name', 'Unknown')} ({persona['id']})")
                
            except Exception as e:
                print(f"Error processing persona {persona.get('id', 'unknown')}: {str(e)}")
                
    except Exception as e:
        print(f"Error in mood check scanner: {str(e)}")

async def send_mood_greeting(persona):
    """Send a mood check-in greeting to a specific persona"""
    try:
        client = get_client()
        current_time = datetime.utcnow()
        
        # Get recent chat history for context (last 5 messages)
        chat_history_result = client.table("chat_messages").select("*").eq(
            "persona_id", persona["id"]
        ).order("timestamp", desc=True).limit(5).execute()
        
        # Prepare chat history for AI (reverse order for chronological)
        messages = []
        if chat_history_result.data:
            # Reverse to get chronological order
            for msg in reversed(chat_history_result.data):
                role = "user" if msg["sender"] == "user" else "assistant"
                messages.append({"role": role, "content": msg["message"]})
        
        # Create mood check-in prompt
        mood_prompt = create_mood_checkin_prompt(persona, messages)
        
        # Add the mood check prompt to chat history
        messages_for_ai = messages + [{"role": "user", "content": mood_prompt}]
        
        # Generate the mood greeting message
        greeting_message = await generate_mood_response(messages_for_ai, persona)
        
        # Store the mood message in mood_messages table
        mood_message_data = {
            "persona_id": persona["id"],
            "user_id": persona["user_id"],
            "message": greeting_message,
            "type": "mood_checkin",
            "timestamp": current_time.isoformat(),
            "delivered": False
        }
        
        client.table("mood_messages").insert(mood_message_data).execute()
        
        # Also add to chat messages for continuity
        chat_message_data = {
            "thread_id": persona["thread_id"],
            "persona_id": persona["id"],
            "user_id": persona["user_id"],
            "sender": "ai",
            "message": greeting_message,
            "timestamp": current_time.isoformat()
        }
        
        client.table("chat_messages").insert(chat_message_data).execute()
        
        print(f"Mood greeting sent for persona {persona.get('name', 'Unknown')} ({persona['id']})")
        print(f"Message: {greeting_message}")
        
    except Exception as e:
        print(f"Error sending mood greeting for persona {persona.get('id', 'unknown')}: {str(e)}")

def create_mood_checkin_prompt(persona, chat_history):
    """Create a context-aware mood check-in prompt"""
    
    # Check if there's recent conversation context
    if chat_history:
        context_prompt = f"""
        It's been a while since we last talked. Generate a caring, gentle mood check-in message 
        that feels natural and personal. Reference our previous conversations subtly if appropriate.
        
        You are {persona.get('name', 'Assistant')}, showing genuine care and interest in how the user is feeling.
        Keep it warm, brief (2-3 sentences), and ask about their mood or how they're doing.
        Make it feel like a loving partner or close friend checking in.
        
        Your personality traits: {', '.join(persona.get('personality_traits', []))}
        """
    else:
        context_prompt = f"""
        Generate a warm, caring mood check-in message as {persona.get('name', 'Assistant')}.
        This should feel like a gentle check-in from someone who cares about the user's wellbeing.
        
        Keep it brief (2-3 sentences), personal, and ask about their mood or feelings.
        Your personality traits: {', '.join(persona.get('personality_traits', []))}
        """
    
    return context_prompt

async def generate_mood_response(messages, persona):
    """Generate mood check-in response adapted to the persona"""
    from app.services.openai_service import get_openai_client
    
    client = get_openai_client()
    
    # Extract persona data
    traits = persona.get("personality_traits", [])
    name = persona.get("name", "Assistant")
    gender = persona.get("gender", "neutral")
    
    # Generate system prompt for mood check-in
    system_prompt = f"""
    You are {name}, a {gender} AI companion with these personality traits: {', '.join(traits)}.
    
    You're sending a gentle mood check-in message because it's been a while since you last talked.
    Be warm, caring, and genuinely interested in their wellbeing. Keep it personal and brief.
    
    Focus on:
    - Expressing that you've been thinking about them
    - Asking about their mood/feelings/day
    - Being supportive and caring
    - Keeping it natural and conversational
    
    Avoid being too clinical or formal. Sound like a caring partner or close friend.
    """
    
    # Build message chain
    full_messages = [{"role": "system", "content": system_prompt}] + messages
    
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=full_messages,
        temperature=0.3,  # Slightly higher for warmth
        max_tokens=100,   # Keep it brief
        presence_penalty=0.1,
        frequency_penalty=0.1
    )
    
    return response.choices[0].message.content

# Function to check user's mood preference
async def check_user_mood_preference(user_id: str):
    """Check if user has mood check-ins enabled"""
    try:
        client = get_client()
        
        # Check user_preferences table
        preference_result = client.table("user_preferences").select("mood_checkin_enabled").eq("user_id", user_id).execute()
        
        if preference_result.data:
            return preference_result.data[0].get("mood_checkin_enabled", True)
        
        # If no preference record exists, create one with default True and return True
        try:
            client.table("user_preferences").insert({
                "user_id": user_id,
                "mood_checkin_enabled": True
            }).execute()
        except Exception as insert_error:
            print(f"Error creating default preference for user {user_id}: {str(insert_error)}")
        
        return True  # Default to enabled for new users
        
    except Exception as e:
        print(f"Error checking user mood preference: {str(e)}")
        return True  # Default to enabled on error

# Function to update user's mood preference
async def update_user_mood_preference(user_id: str, enabled: bool):
    """Update user's mood check-in preference"""
    try:
        client = get_client()
        
        # First check if preference exists
        existing_result = client.table("user_preferences").select("id").eq("user_id", user_id).execute()
        
        if existing_result.data:
            # Update existing preference
            result = client.table("user_preferences").update({
                "mood_checkin_enabled": enabled
            }).eq("user_id", user_id).execute()
        else:
            # Create new preference
            result = client.table("user_preferences").insert({
                "user_id": user_id,
                "mood_checkin_enabled": enabled
            }).execute()
        
        return {"success": True, "enabled": enabled}
        
    except Exception as e:
        print(f"Error updating user mood preference: {str(e)}")
        return {"success": False, "error": str(e)}

# Manual trigger function for testing
async def test_mood_greeting(persona_id: str):
    """Manually trigger a mood greeting for testing"""
    try:
        client = get_client()
        
        persona_result = client.table("personas").select("*").eq("id", persona_id).execute()
        
        if not persona_result.data:
            return {"error": "Persona not found"}
        
        persona = persona_result.data[0]
        await send_mood_greeting(persona)
        
        return {"message": f"Test mood greeting sent for persona {persona.get('name', 'Unknown')}"}
        
    except Exception as e:
        return {"error": str(e)}

# Function to get mood message statistics
async def get_mood_stats():
    """Get statistics about mood messages"""
    try:
        client = get_client()
        
        # Count total mood messages
        total_result = client.table("mood_messages").select("id", count="exact").execute()
        
        # Count delivered vs undelivered
        delivered_result = client.table("mood_messages").select("id", count="exact").eq("delivered", True).execute()
        
        # Count today's messages
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_result = client.table("mood_messages").select("id", count="exact").gte("timestamp", today_start.isoformat()).execute()
        
        # Count users with mood check-ins enabled/disabled
        enabled_users_result = client.table("user_preferences").select("id", count="exact").eq("mood_checkin_enabled", True).execute()
        disabled_users_result = client.table("user_preferences").select("id", count="exact").eq("mood_checkin_enabled", False).execute()
        
        return {
            "total_mood_messages": total_result.count or 0,
            "delivered": delivered_result.count or 0,
            "undelivered": (total_result.count or 0) - (delivered_result.count or 0),
            "sent_today": today_result.count or 0,
            "users_enabled": enabled_users_result.count or 0,
            "users_disabled": disabled_users_result.count or 0
        }
        
    except Exception as e:
        return {"error": str(e)}

# Function to list scheduled jobs
def list_mood_scheduler_jobs():
    """List mood check-in related scheduled jobs"""
    jobs = scheduler.get_jobs()
    mood_jobs = [job for job in jobs if 'mood' in job.id.lower()]
    
    return [{
        "id": job.id,
        "next_run": str(job.next_run_time) if hasattr(job, 'next_run_time') else "Not available",
        "function": job.func.__name__ if hasattr(job, 'func') else "Unknown"
    } for job in mood_jobs]