"""
AI_CONTEXT: Invite code generation and management
Handles creation of unique invite codes for beta access.
"""

import random
import string
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from uuid import UUID

from .client import get_supabase_client
from .models import InviteCode


class InviteManager:
    """
    Manages invite code generation and validation.
    
    AI_CONTEXT: Beta access control
    Generates unique codes per user with usage tracking.
    """
    
    def __init__(self):
        self.client = get_supabase_client()
        
    def generate_code(self, prefix: str = "AGTOS") -> str:
        """
        Generate a unique invite code.
        
        Args:
            prefix: Code prefix (default: AGTOS)
            
        Returns:
            Unique invite code like "AGTOS-XXXX-YYYY"
        """
        segments = []
        for _ in range(2):
            segment = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            segments.append(segment)
        
        return f"{prefix}-{'-'.join(segments)}"
    
    def create_invite(
        self,
        created_by: Optional[UUID] = None,
        expires_days: Optional[int] = 30,
        max_uses: Optional[int] = 1,
        metadata: Optional[dict] = None,
        code: Optional[str] = None
    ) -> Optional[InviteCode]:
        """
        Create a new invite code.
        
        Args:
            created_by: User ID who created the invite
            expires_days: Days until expiration (None = never expires)
            max_uses: Maximum number of uses (None = unlimited)
            metadata: Additional metadata
            code: Specific code to use (auto-generated if None)
            
        Returns:
            Created InviteCode or None on error
        """
        if code is None:
            # Generate unique code
            attempts = 0
            while attempts < 10:
                code = self.generate_code()
                # Check if exists
                existing = self.client.table("invite_codes").select("id").eq("code", code).execute()
                if not existing.data:
                    break
                attempts += 1
            else:
                return None  # Failed to generate unique code
        
        invite_data = {
            "code": code,
            "created_by": str(created_by) if created_by else None,
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=expires_days)).isoformat() if expires_days else None,
            "max_uses": max_uses,
            "metadata": metadata or {}
        }
        
        try:
            response = self.client.table("invite_codes").insert(invite_data).execute()
            if response.data:
                return InviteCode(**response.data[0])
        except:
            pass
        
        return None
    
    def create_bulk_invites(
        self,
        count: int,
        prefix: str = "BETA",
        expires_days: int = 30,
        max_uses: int = 1
    ) -> List[InviteCode]:
        """
        Create multiple invite codes at once.
        
        Args:
            count: Number of codes to create
            prefix: Code prefix
            expires_days: Days until expiration
            max_uses: Uses per code
            
        Returns:
            List of created invite codes
        """
        invites = []
        for i in range(count):
            metadata = {"batch": f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d')}", "index": i + 1}
            invite = self.create_invite(
                expires_days=expires_days,
                max_uses=max_uses,
                metadata=metadata
            )
            if invite:
                invites.append(invite)
        
        return invites
    
    def get_invite_stats(self, code: str) -> Optional[dict]:
        """
        Get usage statistics for an invite code.
        
        Args:
            code: Invite code to check
            
        Returns:
            Dict with usage stats or None
        """
        try:
            # Get invite details
            invite_response = self.client.table("invite_codes").select("*").eq("code", code).single().execute()
            if not invite_response.data:
                return None
            
            invite = InviteCode(**invite_response.data)
            
            # Get usage details
            usage_response = self.client.table("invite_usage").select("*").eq("invite_code_id", str(invite.id)).execute()
            
            return {
                "code": invite.code,
                "is_valid": invite.is_valid,
                "created_at": invite.created_at,
                "expires_at": invite.expires_at,
                "max_uses": invite.max_uses,
                "used_count": invite.used_count,
                "remaining_uses": (invite.max_uses - invite.used_count) if invite.max_uses else "unlimited",
                "usage_details": usage_response.data if usage_response.data else []
            }
        except:
            return None
    
    def deactivate_invite(self, code: str) -> bool:
        """
        Deactivate an invite code.
        
        Args:
            code: Code to deactivate
            
        Returns:
            True if successful
        """
        try:
            response = self.client.table("invite_codes").update({"is_active": False}).eq("code", code).execute()
            return bool(response.data)
        except:
            return False