"""
AI_CONTEXT: Auth data models
Pydantic models for authentication data structures.
"""

from datetime import datetime, timezone
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class User(BaseModel):
    """User account model."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    email: str
    name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    subscription_status: Literal["beta", "free", "pro", "enterprise"] = "beta"
    is_active: bool = True
    last_login: Optional[datetime] = None
    metadata: dict = Field(default_factory=dict)


class InviteCode(BaseModel):
    """Invite code model for beta access."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    code: str
    created_by: Optional[UUID] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    max_uses: Optional[int] = None
    used_count: int = 0
    is_active: bool = True
    metadata: dict = Field(default_factory=dict)
    
    @property
    def is_valid(self) -> bool:
        """Check if invite code is still valid."""
        if not self.is_active:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        if self.max_uses is not None and self.used_count >= self.max_uses:
            return False
        return True


class AuthToken(BaseModel):
    """Auth token for offline access."""
    model_config = ConfigDict(from_attributes=True)
    
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: datetime
    user_id: UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now(timezone.utc) > self.expires_at


class InviteUsage(BaseModel):
    """Track invite code usage."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    invite_code_id: UUID
    user_id: UUID
    used_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None