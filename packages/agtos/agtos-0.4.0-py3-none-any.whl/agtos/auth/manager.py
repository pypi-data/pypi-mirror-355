"""
AI_CONTEXT: Authentication manager
Core auth operations including signup, login, and token management.
"""

import os
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Tuple
from uuid import uuid4

from .client import get_supabase_client, get_anon_client
from .models import User, InviteCode, AuthToken
from .token import TokenStore


class AuthManager:
    """
    Manages authentication operations for agtOS.
    
    AI_CONTEXT: Central auth orchestration
    Handles user signup, login, token management, and offline access.
    """
    
    def __init__(self):
        self.client = get_supabase_client()
        self.anon_client = get_anon_client()
        self.token_store = TokenStore()
        
    def validate_invite_code(self, code: str) -> Optional[InviteCode]:
        """
        Validate an invite code.
        
        Args:
            code: Invite code to validate
            
        Returns:
            InviteCode if valid, None otherwise
        """
        try:
            response = self.client.table("invite_codes").select("*").eq("code", code).single().execute()
            if response.data:
                invite = InviteCode(**response.data)
                return invite if invite.is_valid else None
        except:
            pass
        return None
    
    def signup_with_invite(self, email: str, password: str, invite_code: str, name: Optional[str] = None) -> Tuple[Optional[User], Optional[str]]:
        """
        Sign up a new user with an invite code.
        
        Args:
            email: User email
            password: User password
            invite_code: Valid invite code
            name: Optional user name
            
        Returns:
            Tuple of (User, error_message)
        """
        # Validate invite code
        invite = self.validate_invite_code(invite_code)
        if not invite:
            return None, "Invalid or expired invite code"
        
        try:
            # Sign up with Supabase Auth
            auth_response = self.anon_client.auth.sign_up({
                "email": email,
                "password": password,
            })
            
            if not auth_response.user:
                return None, "Failed to create account"
            
            user_id = auth_response.user.id
            
            # Create user profile
            now = datetime.now(timezone.utc)
            user_data = {
                "id": user_id,
                "email": email,
                "name": name,
                "created_at": now,
                "updated_at": now,
                "subscription_status": "beta",
                "metadata": {"invite_code": invite_code}
            }
            
            # Insert only the database fields
            db_data = {
                "id": user_id,
                "email": email,
                "name": name,
                "subscription_status": "beta",
                "metadata": {"invite_code": invite_code}
            }
            self.client.table("users").insert(db_data).execute()
            
            # Use the invite code
            self.client.rpc("validate_and_use_invite_code", {
                "p_code": invite_code,
                "p_user_id": user_id
            }).execute()
            
            # Store auth token
            if auth_response.session:
                token = AuthToken(
                    access_token=auth_response.session.access_token,
                    refresh_token=auth_response.session.refresh_token,
                    expires_at=datetime.fromtimestamp(auth_response.session.expires_at),
                    user_id=user_id
                )
                self.token_store.save_token(token)
            
            return User(**user_data), None
            
        except Exception as e:
            return None, str(e)
    
    def login(self, email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
        """
        Log in an existing user.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Tuple of (User, error_message)
        """
        try:
            auth_response = self.anon_client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if not auth_response.user:
                return None, "Invalid credentials"
            
            user_id = auth_response.user.id
            
            # Get user profile
            user_response = self.client.table("users").select("*").eq("id", user_id).single().execute()
            if not user_response.data:
                return None, "User profile not found"
            
            user = User(**user_response.data)
            
            # Update last login
            self.client.table("users").update({"last_login": datetime.now(timezone.utc).isoformat()}).eq("id", user_id).execute()
            
            # Store auth token
            if auth_response.session:
                token = AuthToken(
                    access_token=auth_response.session.access_token,
                    refresh_token=auth_response.session.refresh_token,
                    expires_at=datetime.fromtimestamp(auth_response.session.expires_at),
                    user_id=user_id
                )
                self.token_store.save_token(token)
            
            return user, None
            
        except Exception as e:
            return None, str(e)
    
    def get_current_user(self) -> Optional[User]:
        """
        Get current authenticated user from stored token.
        
        Returns:
            User if authenticated, None otherwise
        """
        token = self.token_store.get_valid_token()
        if not token:
            return None
        
        try:
            # Set auth header and get user
            self.anon_client.auth.set_session(token.access_token, token.refresh_token)
            user_response = self.anon_client.auth.get_user()
            
            if user_response and user_response.user:
                # Get full profile
                profile_response = self.client.table("users").select("*").eq("id", user_response.user.id).single().execute()
                if profile_response.data:
                    return User(**profile_response.data)
        except:
            pass
        
        return None
    
    def logout(self):
        """Log out current user and clear stored tokens."""
        try:
            self.anon_client.auth.sign_out()
        except:
            pass
        self.token_store.clear_tokens()
    
    def check_auth_required(self) -> bool:
        """
        Check if authentication is required.
        
        Returns:
            True if auth is required (no valid token), False otherwise
        """
        return self.get_current_user() is None
    
    def refresh_token(self) -> bool:
        """
        Refresh the current auth token.
        
        Returns:
            True if refresh successful, False otherwise
        """
        token = self.token_store.get_token()
        if not token or not token.refresh_token:
            return False
        
        try:
            self.anon_client.auth.set_session(token.access_token, token.refresh_token)
            session = self.anon_client.auth.refresh_session()
            
            if session and session.access_token:
                new_token = AuthToken(
                    access_token=session.access_token,
                    refresh_token=session.refresh_token,
                    expires_at=datetime.fromtimestamp(session.expires_at),
                    user_id=token.user_id
                )
                self.token_store.save_token(new_token)
                return True
        except:
            pass
        
        return False