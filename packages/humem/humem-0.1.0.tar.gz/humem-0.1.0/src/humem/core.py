"""Core agent memory management system."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from uuid import UUID

from .models import Memory, MemoryType, MemoryQuery, MemoryUpdate
from .storage import MemoryStorage
from .exceptions import MemoryError, MemoryNotFoundError, MemoryValidationError


class AgentMemory:
    """
    Main interface for the agent memory system.
    
    Provides high-level methods for storing, retrieving, and managing
    memories for AI agents and their interactions with users.
    """
    
    def __init__(self, database_url: str = None, auto_cleanup: bool = True):
        """
        Initialize the agent memory system.
        
        Args:
            database_url: Database connection URL. Defaults to SQLite.
            auto_cleanup: Whether to automatically clean up expired memories.
        """
        self.storage = MemoryStorage(database_url)
        self.auto_cleanup = auto_cleanup
        
        if self.auto_cleanup:
            self._cleanup_expired()
    
    def add_memory(
        self,
        user_id: str,
        content: str,
        memory_type: MemoryType = MemoryType.CONVERSATION,
        agent_id: Optional[str] = None,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        expires_in_days: Optional[int] = None,
    ) -> Memory:
        """
        Add a new memory to the system.
        
        Args:
            user_id: Unique identifier for the user
            content: The memory content
            memory_type: Type of memory (default: CONVERSATION)
            agent_id: Optional agent identifier
            importance: Importance score (0.0 to 1.0)
            tags: Optional list of tags
            metadata: Optional metadata dictionary
            expires_in_days: Number of days until memory expires
        
        Returns:
            The created Memory object
        """
        if not user_id or not content:
            raise MemoryValidationError("user_id and content are required")
        
        if not (0.0 <= importance <= 1.0):
            raise MemoryValidationError("importance must be between 0.0 and 1.0")
        
        expires_at = None
        if expires_in_days is not None:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        memory = Memory(
            user_id=user_id,
            agent_id=agent_id,
            memory_type=memory_type,
            content=content,
            importance=importance,
            tags=tags or [],
            metadata=metadata or {},
            expires_at=expires_at,
        )
        
        return self.storage.add_memory(memory)
    
    def get_memory(self, memory_id: Union[str, UUID]) -> Memory:
        """
        Retrieve a memory by its ID.
        
        Args:
            memory_id: The memory ID
        
        Returns:
            The Memory object
        
        Raises:
            MemoryNotFoundError: If memory doesn't exist
        """
        return self.storage.get_memory(memory_id)
    
    def update_memory(
        self,
        memory_id: Union[str, UUID],
        content: Optional[str] = None,
        importance: Optional[float] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        expires_in_days: Optional[int] = None,
    ) -> Memory:
        """
        Update an existing memory.
        
        Args:
            memory_id: The memory ID to update
            content: New content (optional)
            importance: New importance score (optional)
            tags: New tags list (optional)
            metadata: New metadata dict (optional)
            expires_in_days: New expiration in days (optional)
        
        Returns:
            The updated Memory object
        """
        update_data = {}
        
        if content is not None:
            update_data["content"] = content
        
        if importance is not None:
            if not (0.0 <= importance <= 1.0):
                raise MemoryValidationError("importance must be between 0.0 and 1.0")
            update_data["importance"] = importance
        
        if tags is not None:
            update_data["tags"] = tags
        
        if metadata is not None:
            update_data["metadata"] = metadata
        
        if expires_in_days is not None:
            update_data["expires_at"] = datetime.utcnow() + timedelta(days=expires_in_days)
        
        if not update_data:
            raise MemoryValidationError("At least one field must be provided for update")
        
        update = MemoryUpdate(**update_data)
        return self.storage.update_memory(memory_id, update)
    
    def delete_memory(self, memory_id: Union[str, UUID]) -> bool:
        """
        Delete a memory by its ID.
        
        Args:
            memory_id: The memory ID to delete
        
        Returns:
            True if memory was deleted, False if not found
        """
        return self.storage.delete_memory(memory_id)
    
    def search_memories(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        content_search: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_importance: Optional[float] = None,
        max_importance: Optional[float] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
        include_expired: bool = False,
    ) -> List[Memory]:
        """
        Search for memories based on various criteria.
        
        Args:
            user_id: Filter by user ID
            agent_id: Filter by agent ID
            memory_type: Filter by memory type
            content_search: Search in memory content
            tags: Filter by tags (any match)
            min_importance: Minimum importance score
            max_importance: Maximum importance score
            created_after: Only memories created after this date
            created_before: Only memories created before this date
            limit: Maximum number of results
            offset: Number of results to skip
            include_expired: Whether to include expired memories
        
        Returns:
            List of matching Memory objects
        """
        query = MemoryQuery(
            user_id=user_id,
            agent_id=agent_id,
            memory_type=memory_type,
            content_search=content_search,
            tags=tags,
            min_importance=min_importance,
            max_importance=max_importance,
            created_after=created_after,
            created_before=created_before,
            limit=limit,
            offset=offset,
            include_expired=include_expired,
        )
        
        return self.storage.search_memories(query)
    
    def get_user_memories(
        self,
        user_id: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 50,
    ) -> List[Memory]:
        """
        Get all memories for a specific user.
        
        Args:
            user_id: The user ID
            memory_type: Optional memory type filter
            limit: Maximum number of results
        
        Returns:
            List of Memory objects for the user
        """
        return self.search_memories(
            user_id=user_id,
            memory_type=memory_type,
            limit=limit
        )
    
    def add_conversation_memory(
        self,
        user_id: str,
        user_message: str,
        agent_response: str,
        agent_id: Optional[str] = None,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
    ) -> Memory:
        """
        Add a conversation memory with both user message and agent response.
        
        Args:
            user_id: The user ID
            user_message: What the user said
            agent_response: How the agent responded
            agent_id: Optional agent ID
            importance: Importance score
            tags: Optional tags
        
        Returns:
            The created Memory object
        """
        content = f"User: {user_message}\nAgent: {agent_response}"
        metadata = {
            "user_message": user_message,
            "agent_response": agent_response,
            "conversation": True,
        }
        
        return self.add_memory(
            user_id=user_id,
            content=content,
            memory_type=MemoryType.CONVERSATION,
            agent_id=agent_id,
            importance=importance,
            tags=tags,
            metadata=metadata,
        )
    
    def add_user_preference(
        self,
        user_id: str,
        preference: str,
        value: Any,
        agent_id: Optional[str] = None,
        importance: float = 0.8,
    ) -> Memory:
        """
        Add a user preference memory.
        
        Args:
            user_id: The user ID
            preference: The preference name
            value: The preference value
            agent_id: Optional agent ID
            importance: Importance score (defaults to high)
        
        Returns:
            The created Memory object
        """
        content = f"User preference: {preference} = {value}"
        metadata = {
            "preference_name": preference,
            "preference_value": value,
        }
        
        return self.add_memory(
            user_id=user_id,
            content=content,
            memory_type=MemoryType.USER_PREFERENCE,
            agent_id=agent_id,
            importance=importance,
            tags=["preference", preference],
            metadata=metadata,
        )
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get all user preferences as a dictionary.
        
        Args:
            user_id: The user ID
        
        Returns:
            Dictionary of preference names to values
        """
        memories = self.search_memories(
            user_id=user_id,
            memory_type=MemoryType.USER_PREFERENCE
        )
        
        preferences = {}
        for memory in memories:
            if "preference_name" in memory.metadata:
                pref_name = memory.metadata["preference_name"]
                pref_value = memory.metadata.get("preference_value")
                preferences[pref_name] = pref_value
        
        return preferences
    
    def cleanup_expired(self) -> int:
        """
        Manually clean up expired memories.
        
        Returns:
            Number of memories cleaned up
        """
        return self.storage.cleanup_expired_memories()
    
    def _cleanup_expired(self) -> None:
        """Internal method to clean up expired memories."""
        try:
            self.storage.cleanup_expired_memories()
        except Exception:
            # Silently fail on cleanup errors
            pass
    
    def get_memory_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about stored memories.
        
        Args:
            user_id: Optional user ID to filter stats
        
        Returns:
            Dictionary with memory statistics
        """
        all_memories = self.search_memories(
            user_id=user_id,
            limit=1000,  # Get up to 1000 for stats
            include_expired=True
        )
        
        stats = {
            "total_memories": len(all_memories),
            "by_type": {},
            "by_importance": {
                "high": 0,
                "medium": 0,
                "low": 0,
            },
            "expired": 0,
            "total_access_count": 0,
        }
        
        for memory in all_memories:
            # Count by type
            type_name = memory.memory_type.value
            stats["by_type"][type_name] = stats["by_type"].get(type_name, 0) + 1
            
            # Count by importance
            if memory.importance >= 0.7:
                stats["by_importance"]["high"] += 1
            elif memory.importance >= 0.4:
                stats["by_importance"]["medium"] += 1
            else:
                stats["by_importance"]["low"] += 1
            
            # Count expired
            if memory.is_expired():
                stats["expired"] += 1
            
            # Sum access counts
            stats["total_access_count"] += memory.access_count
        
        return stats 