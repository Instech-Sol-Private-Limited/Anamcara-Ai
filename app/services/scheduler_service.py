from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from services.openai_service import generate_chat_response
from utils.prompt_generation import generate_personality_prompt
from bson import ObjectId
import pytz
from scheduler_instance import scheduler

async def schedule_daily_greeting(persona_id: str):
    # Set timezone to Pakistan Standard Time (PST)
    pakistan_tz = pytz.timezone('Asia/Karachi')
    
    # Schedule for 3:42 PM Pakistan time for testing
    scheduler.add_job(
        send_daily_greeting, 
        CronTrigger(hour=16, minute=31, timezone=pakistan_tz), 
        args=[persona_id], 
        id=f"daily_greeting_{persona_id}", 
        replace_existing=True
    )
    print(f"Scheduled daily greeting for persona {persona_id} at 3:42 PM Pakistan time")

async def send_daily_greeting(persona_id: str):
    try:
        # Import and ensure db connection
        from database.mongodb import ensure_db_connection
        
        db = await ensure_db_connection()
        if db is None:
            print("Database connection is not available")
            return
            
        # Get persona details
        persona = await db.personas.find_one({"_id": ObjectId(persona_id)})
        if not persona:
            print(f"Persona {persona_id} not found")
            return

        # Get chat history for this persona and thread
        user_chat = await db.chats.find_one({"user_id": persona["user_id"]})
        chat_history = []
        
        if user_chat:
            # Find the specific thread for this persona
            for thread in user_chat.get("threads", []):
                if thread["thread_id"] == persona["thread_id"]:
                    # Get recent chat history (last 10 messages)
                    recent_messages = thread["messages"][-10:] if len(thread["messages"]) > 10 else thread["messages"]
                    
                    # Convert to OpenAI format
                    for msg in recent_messages:
                        role = "user" if msg["sender"] == "user" else "assistant"
                        chat_history.append({
                            "role": role,
                            "content": msg["message"]
                        })
                    break

        # Create context-aware prompt based on chat history
        if chat_history:
            context_prompt = f"""
            Based on our previous conversations, generate a warm, caring daily greeting message. 
            Consider the context of our past interactions and make it personal and meaningful.
            Keep it brief but heartfelt. Make it feel like a natural continuation of our relationship.
            
            Recent conversation context: You are {persona['name']}, a {persona['gender']} with these traits: {', '.join(persona['personality_traits'])}.
            """
        else:
            context_prompt = f"""
            Generate a warm, caring daily greeting message as {persona['name']}, a {persona['gender']} with these personality traits: {', '.join(persona['personality_traits'])}.
            This is one of our first interactions, so make it welcoming and introduce yourself naturally.
            Keep it brief but personal and loving.
            """

        # Add the greeting prompt to chat history
        messages_for_ai = chat_history + [{"role": "user", "content": context_prompt}]
        
        # Generate the greeting message
        greeting_message = await generate_chat_response(messages_for_ai, persona)

        # Store the daily message in daily_messages collection
        await db.daily_messages.insert_one({
            "persona_id": persona_id,
            "thread_id": persona["thread_id"],
            "message": greeting_message,
            "type": "daily_greeting",
            "timestamp": datetime.utcnow(),
            "delivered": False,
            "user_id": persona["user_id"]
        })

        # Add the greeting to the chat thread
        greeting_entry = {
            "sender": "ai",
            "message": greeting_message,
            "timestamp": datetime.utcnow()
        }

        # Update or create chat thread with the greeting
        if user_chat:
            # Find and update the existing thread
            thread_found = False
            for thread in user_chat["threads"]:
                if thread["thread_id"] == persona["thread_id"]:
                    thread["messages"].append(greeting_entry)
                    thread_found = True
                    break
            
            if thread_found:
                await db.chats.replace_one({"_id": user_chat["_id"]}, user_chat)
            else:
                # Create new thread if not found
                new_thread = {
                    "thread_id": persona["thread_id"],
                    "persona_id": persona_id,
                    "messages": [greeting_entry]
                }
                await db.chats.update_one(
                    {"user_id": persona["user_id"]},
                    {"$push": {"threads": new_thread}}
                )
        else:
            # Create new chat document
            new_chat = {
                "user_id": persona["user_id"],
                "threads": [{
                    "thread_id": persona["thread_id"],
                    "persona_id": persona_id,
                    "messages": [greeting_entry]
                }]
            }
            await db.chats.insert_one(new_chat)

        # Update persona's last interaction
        await db.personas.update_one(
            {"_id": ObjectId(persona_id)},
            {"$set": {"last_interaction": datetime.utcnow()}}
        )

        print(f"Daily greeting sent for persona {persona['name']} ({persona_id})")
        print(f"Message: {greeting_message}")

    except Exception as e:
        print(f"Error sending daily greeting for persona {persona_id}: {str(e)}")

# Optional: Function to manually trigger greeting for testing
async def test_daily_greeting(persona_id: str):
    """Manually trigger a daily greeting for testing purposes"""
    print(f"Testing daily greeting for persona {persona_id}")
    
    # Import and ensure db connection
    from database.mongodb import ensure_db_connection
    
    db = await ensure_db_connection()
    if db is None:
        print("Database connection is not available")
        return {"error": "Database connection not available"}
    
    await send_daily_greeting(persona_id)

# Optional: Function to list all scheduled jobs
def list_scheduled_jobs():
    """List all currently scheduled jobs"""
    jobs = scheduler.get_jobs()
    print(f"Currently scheduled jobs: {len(jobs)}")
    for job in jobs:
        try:
            # Get next run time - different methods depending on APScheduler version
            next_run = getattr(job, 'next_run_time', None)
            if next_run is None:
                # Try alternative method for newer versions
                next_run = job.next_run_time if hasattr(job, 'next_run_time') else "Not available"
        except:
            next_run = "Not available"
        
        print(f"Job ID: {job.id}, Next run: {next_run}")
    return jobs