"""Data models for agent memory system."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """Types of memories that can be stored."""
    
    USER_PREFERENCE = "user_preference"
    CONVERSATION = "conversation"
    FACT = "fact"
    CONTEXT = "context"
    GOAL = "goal"
    FEEDBACK = "feedback"


class Memory(BaseModel):
    """A memory entry in the agent memory system."""
    
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the memory")
    user_id: str = Field(..., description="Identifier for the user this memory belongs to")
    agent_id: Optional[str] = Field(default=None, description="Identifier for the agent")
    memory_type: MemoryType = Field(..., description="Type of memory")
    content: str = Field(..., description="The actual memory content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    importance: float = Field(default=0.5, ge=0.0, le=1.0, description="Importance score (0.0 to 1.0)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the memory was created")
    last_accessed: Optional[datetime] = Field(default=None, description="When the memory was last accessed")
    access_count: int = Field(default=0, description="Number of times this memory has been accessed")
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing memories")
    expires_at: Optional[datetime] = Field(default=None, description="When this memory expires")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str,
        }
    
    def is_expired(self) -> bool:
        """Check if the memory has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def update_access(self) -> None:
        """Update access statistics."""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1


class MemoryQuery(BaseModel):
    """Query parameters for searching memories."""
    
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    memory_type: Optional[MemoryType] = None
    tags: Optional[List[str]] = None
    content_search: Optional[str] = None
    min_importance: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    max_importance: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    include_expired: bool = Field(default=False)


class MemoryUpdate(BaseModel):
    """Model for updating memory fields."""
    
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    importance: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    tags: Optional[List[str]] = None
    expires_at: Optional[datetime] = None 