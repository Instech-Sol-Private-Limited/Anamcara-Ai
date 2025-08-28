# models/supabase_helpers.py
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

def serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Supabase response to match expected format"""
    if doc and 'id' in doc:
        # Convert UUID to string if needed
        if isinstance(doc['id'], uuid.UUID):
            doc['id'] = str(doc['id'])
        
        # Convert datetime objects to ISO string format
        for key, value in doc.items():
            if isinstance(value, datetime):
                doc[key] = value.isoformat()
    
    return doc

def serialize_docs(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Serialize a list of documents"""
    return [serialize_doc(doc) for doc in docs]

def prepare_chat_thread_data(user_id: str, thread_id: str, persona_id: str, 
                           user_message: str, ai_response: str, timestamp: datetime) -> List[Dict[str, Any]]:
    """Prepare chat messages for insertion into chat_messages table"""
    messages = [
        {
            'thread_id': thread_id,
            'persona_id': persona_id,
            'user_id': user_id,
            'sender': 'user',
            'message': user_message,
            'timestamp': timestamp.isoformat()
        },
        {
            'thread_id': thread_id,
            'persona_id': persona_id,
            'user_id': user_id,
            'sender': 'ai',
            'message': ai_response,
            'timestamp': timestamp.isoformat()
        }
    ]
    return messages

def convert_personality_traits_to_array(traits: List[str]) -> List[str]:
    """Convert personality traits list to PostgreSQL array format"""
    return traits

def convert_form_data_to_arrays(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert form data lists to PostgreSQL arrays"""
    converted_data = {}
    for key, value in data.items():
        if isinstance(value, list):
            converted_data[key] = value
        else:
            converted_data[key] = value
    return converted_data