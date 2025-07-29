"""Tests for core AgentMemory functionality."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from humem import AgentMemory, MemoryType, MemoryError, MemoryNotFoundError


@pytest.fixture
def memory_system():
    """Create a test memory system with in-memory database."""
    return AgentMemory(database_url="sqlite:///:memory:", auto_cleanup=False)


@pytest.fixture
def sample_user_id():
    """Get a sample user ID for testing."""
    return "test_user_123"


class TestAgentMemory:
    """Test cases for AgentMemory class."""
    
    def test_add_memory(self, memory_system, sample_user_id):
        """Test adding a basic memory."""
        memory = memory_system.add_memory(
            user_id=sample_user_id,
            content="Test memory content",
            memory_type=MemoryType.FACT,
            importance=0.8,
            tags=["test", "fact"]
        )
        
        assert memory.user_id == sample_user_id
        assert memory.content == "Test memory content"
        assert memory.memory_type == MemoryType.FACT
        assert memory.importance == 0.8
        assert memory.tags == ["test", "fact"]
        assert memory.id is not None
    
    def test_get_memory(self, memory_system, sample_user_id):
        """Test retrieving a memory by ID."""
        # Add a memory
        original_memory = memory_system.add_memory(
            user_id=sample_user_id,
            content="Retrievable memory"
        )
        
        # Retrieve it
        retrieved_memory = memory_system.get_memory(original_memory.id)
        
        assert retrieved_memory.id == original_memory.id
        assert retrieved_memory.content == "Retrievable memory"
        assert retrieved_memory.access_count == 1  # Should increment on access
    
    def test_get_nonexistent_memory(self, memory_system):
        """Test retrieving a non-existent memory raises error."""
        fake_id = uuid4()
        with pytest.raises(MemoryNotFoundError):
            memory_system.get_memory(fake_id)
    
    def test_update_memory(self, memory_system, sample_user_id):
        """Test updating a memory."""
        # Add a memory
        memory = memory_system.add_memory(
            user_id=sample_user_id,
            content="Original content",
            importance=0.5
        )
        
        # Update it
        updated_memory = memory_system.update_memory(
            memory.id,
            content="Updated content",
            importance=0.9,
            tags=["updated"]
        )
        
        assert updated_memory.content == "Updated content"
        assert updated_memory.importance == 0.9
        assert updated_memory.tags == ["updated"]
    
    def test_delete_memory(self, memory_system, sample_user_id):
        """Test deleting a memory."""
        # Add a memory
        memory = memory_system.add_memory(
            user_id=sample_user_id,
            content="To be deleted"
        )
        
        # Delete it
        result = memory_system.delete_memory(memory.id)
        assert result is True
        
        # Verify it's gone
        with pytest.raises(MemoryNotFoundError):
            memory_system.get_memory(memory.id)
    
    def test_search_memories(self, memory_system, sample_user_id):
        """Test searching for memories."""
        # Add multiple memories
        memory_system.add_memory(
            user_id=sample_user_id,
            content="Python programming tips",
            memory_type=MemoryType.FACT,
            tags=["programming", "python"]
        )
        memory_system.add_memory(
            user_id=sample_user_id,
            content="JavaScript is also useful",
            memory_type=MemoryType.FACT,
            tags=["programming", "javascript"]
        )
        memory_system.add_memory(
            user_id=sample_user_id,
            content="I like coffee",
            memory_type=MemoryType.USER_PREFERENCE,
            tags=["preference", "coffee"]
        )
        
        # Search by user_id
        all_memories = memory_system.search_memories(user_id=sample_user_id)
        assert len(all_memories) == 3
        
        # Search by memory type
        facts = memory_system.search_memories(
            user_id=sample_user_id,
            memory_type=MemoryType.FACT
        )
        assert len(facts) == 2
        
        # Search by content
        python_memories = memory_system.search_memories(
            user_id=sample_user_id,
            content_search="Python"
        )
        assert len(python_memories) == 1
        
        # Search by tags
        programming_memories = memory_system.search_memories(
            user_id=sample_user_id,
            tags=["programming"]
        )
        assert len(programming_memories) == 2
    
    def test_add_conversation_memory(self, memory_system, sample_user_id):
        """Test adding conversation memory."""
        memory = memory_system.add_conversation_memory(
            user_id=sample_user_id,
            user_message="How do I learn Python?",
            agent_response="Start with basic syntax and practice regularly.",
            agent_id="helpful_bot"
        )
        
        assert memory.memory_type == MemoryType.CONVERSATION
        assert "User: How do I learn Python?" in memory.content
        assert "Agent: Start with basic syntax" in memory.content
        assert memory.metadata["conversation"] is True
        assert memory.agent_id == "helpful_bot"
    
    def test_add_user_preference(self, memory_system, sample_user_id):
        """Test adding user preference."""
        memory = memory_system.add_user_preference(
            user_id=sample_user_id,
            preference="language",
            value="English"
        )
        
        assert memory.memory_type == MemoryType.USER_PREFERENCE
        assert "preference" in memory.tags
        assert "language" in memory.tags
        assert memory.metadata["preference_name"] == "language"
        assert memory.metadata["preference_value"] == "English"
    
    def test_get_user_preferences(self, memory_system, sample_user_id):
        """Test getting user preferences as dictionary."""
        # Add multiple preferences
        memory_system.add_user_preference(sample_user_id, "language", "English")
        memory_system.add_user_preference(sample_user_id, "theme", "dark")
        memory_system.add_user_preference(sample_user_id, "notifications", True)
        
        preferences = memory_system.get_user_preferences(sample_user_id)
        
        assert preferences["language"] == "English"
        assert preferences["theme"] == "dark"
        assert preferences["notifications"] is True
    
    def test_memory_expiration(self, memory_system, sample_user_id):
        """Test memory expiration functionality."""
        # Add memory that expires in 1 day
        memory = memory_system.add_memory(
            user_id=sample_user_id,
            content="Expires soon",
            expires_in_days=1
        )
        
        assert memory.expires_at is not None
        assert not memory.is_expired()
        
        # Manually set expiration to past
        past_time = datetime.utcnow() - timedelta(days=1)
        memory_system.update_memory(
            memory.id,
            expires_in_days=-1  # This should set expiration to past
        )
        
        # Search without including expired
        memories = memory_system.search_memories(
            user_id=sample_user_id,
            include_expired=False
        )
        assert len(memories) == 0
        
        # Search including expired
        memories_with_expired = memory_system.search_memories(
            user_id=sample_user_id,
            include_expired=True
        )
        assert len(memories_with_expired) == 1
    
    def test_memory_stats(self, memory_system, sample_user_id):
        """Test memory statistics."""
        # Add various memories
        memory_system.add_memory(
            user_id=sample_user_id,
            content="High importance",
            importance=0.9
        )
        memory_system.add_memory(
            user_id=sample_user_id,
            content="Medium importance",
            importance=0.5
        )
        memory_system.add_memory(
            user_id=sample_user_id,
            content="Low importance",
            importance=0.2
        )
        
        stats = memory_system.get_memory_stats(user_id=sample_user_id)
        
        assert stats["total_memories"] == 3
        assert stats["by_importance"]["high"] == 1
        assert stats["by_importance"]["medium"] == 1
        assert stats["by_importance"]["low"] == 1
    
    def test_validation_errors(self, memory_system):
        """Test validation error handling."""
        # Test empty user_id
        with pytest.raises(MemoryError):
            memory_system.add_memory(user_id="", content="test")
        
        # Test empty content
        with pytest.raises(MemoryError):
            memory_system.add_memory(user_id="user", content="")
        
        # Test invalid importance
        with pytest.raises(MemoryError):
            memory_system.add_memory(
                user_id="user",
                content="test",
                importance=1.5  # Invalid: > 1.0
            ) 