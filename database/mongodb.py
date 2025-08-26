
from motor.motor_asyncio import AsyncIOMotorClient
import os

client = None
db = None

async def connect_db():
    global client, db
    mongo_url = os.getenv("MONGODB_URL")
    if not mongo_url:
        raise ValueError("MONGODB_URL environment variable not set")
    
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client["destiny_ai"]
        
        # Test the connection
        await client.admin.command('ping')
        print("Database connected successfully")
        
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        raise

async def close_db():
    global client, db
    if client:
        client.close()
        client = None
        db = None
        print("Database connection closed")

def get_db():
    """Get the current database instance"""
    global db
    if db is None:
        print("Warning: Database is not connected")
    return db

async def ensure_db_connection():
    """Ensure database connection is available"""
    global db
    if db is None:
        print("Database not connected, attempting to reconnect...")
        await connect_db()
    return db