"""
AI_CONTEXT: Supabase client initialization
Manages secure connection to Supabase with proper credential handling.
"""

import os
from typing import Optional
from pathlib import Path
import dotenv
from supabase import create_client, Client

# Load environment variables from .env.local
env_path = Path(__file__).parent.parent.parent / ".env.local"
if env_path.exists():
    dotenv.load_dotenv(env_path)

_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get or create Supabase client instance.
    
    AI_CONTEXT: Singleton pattern for Supabase client
    Ensures single connection instance throughout app lifecycle.
    Uses service key for admin operations when available.
    
    Returns:
        Supabase client instance
        
    Raises:
        ValueError: If required environment variables are missing
    """
    global _client
    
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        service_key = os.getenv("SUPABASE_SERVICE_KEY")
        anon_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url:
            raise ValueError("SUPABASE_URL not found in environment")
        
        # Use service key for admin operations if available
        key = service_key or anon_key
        if not key:
            raise ValueError("Neither SUPABASE_SERVICE_KEY nor SUPABASE_ANON_KEY found")
        
        _client = create_client(url, key)
    
    return _client


def get_anon_client() -> Client:
    """
    Get Supabase client with anon key for user operations.
    
    AI_CONTEXT: Separate client for user-facing operations
    Uses anon key to ensure proper RLS (Row Level Security) enforcement.
    
    Returns:
        Supabase client with anon key
    """
    url = os.getenv("SUPABASE_URL")
    anon_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not anon_key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY required")
    
    return create_client(url, anon_key)