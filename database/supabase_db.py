# database/supabase_db.py
from supabase import create_client, Client
import os
import asyncio
from typing import Optional

client: Optional[Client] = None

def connect_db():
    """Initialize Supabase client"""
    global client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY environment variables must be set")
    
    try:
        client = create_client(supabase_url, supabase_key)
        print("Supabase client initialized successfully")
        return client
    except Exception as e:
        print(f"Failed to initialize Supabase client: {e}")
        raise

def get_client() -> Client:
    """Get the current Supabase client instance"""
    global client
    if client is None:
        print("Warning: Supabase client is not initialized")
        connect_db()
    return client

def close_db():
    """Close database connection (Supabase doesn't require explicit closing)"""
    global client
    client = None
    print("Supabase client connection closed")

async def ensure_db_connection() -> Client:
    """Ensure database connection is available"""
    global client
    if client is None:
        print("Supabase client not initialized, attempting to connect...")
        connect_db()
    return client