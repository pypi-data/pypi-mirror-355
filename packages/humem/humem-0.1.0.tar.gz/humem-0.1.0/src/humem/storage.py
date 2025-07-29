"""Storage backend for agent memory system using SQLAlchemy."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union
from uuid import UUID

from sqlalchemy import (
    Column, String, Text, Float, Integer, DateTime, Boolean, JSON, 
    create_engine, and_, or_, desc
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.types import TypeDecorator, CHAR

from .exceptions import MemoryStorageError, MemoryNotFoundError
from .models import Memory, MemoryQuery, MemoryType, MemoryUpdate

Base = declarative_base()


class GUID(TypeDecorator):
    """Platform-independent GUID type."""
    
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgresUUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, UUID):
                return str(UUID(value))
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, UUID):
                return UUID(value)
            return value


class MemoryRecord(Base):
    """SQLAlchemy model for memory records."""
    
    __tablename__ = 'memories'
    
    id = Column(GUID(), primary_key=True)
    user_id = Column(String(255), nullable=False, index=True)
    agent_id = Column(String(255), nullable=True, index=True)
    memory_type = Column(String(50), nullable=False, index=True)
    content = Column(Text, nullable=False)
    meta_data = Column(JSON, default=dict)
    importance = Column(Float, default=0.5, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    last_accessed = Column(DateTime, nullable=True)
    access_count = Column(Integer, default=0)
    tags = Column(JSON, default=list)
    expires_at = Column(DateTime, nullable=True, index=True)
    
    def to_memory(self) -> Memory:
        """Convert database record to Memory model."""
        return Memory(
            id=self.id,
            user_id=self.user_id,
            agent_id=self.agent_id,
            memory_type=MemoryType(self.memory_type),
            content=self.content,
            metadata=self.meta_data or {},
            importance=self.importance,
            timestamp=self.timestamp,
            last_accessed=self.last_accessed,
            access_count=self.access_count,
            tags=self.tags or [],
            expires_at=self.expires_at,
        )


class MemoryStorage:
    """Storage backend for managing memories in a database."""
    
    def __init__(self, database_url: str = None):
        """
        Initialize the memory storage.
        
        Args:
            database_url: Database connection URL. Defaults to SQLite in memory.
        """
        if database_url is None:
            # Default to SQLite file database
            db_path = Path.home() / ".humem" / "memories.db"
            db_path.parent.mkdir(exist_ok=True)
            database_url = f"sqlite:///{db_path}"
        
        try:
            self.engine = create_engine(database_url, echo=False)
            self.SessionLocal = sessionmaker(bind=self.engine)
            Base.metadata.create_all(self.engine)
        except Exception as e:
            raise MemoryStorageError(f"Failed to initialize database: {str(e)}", e)
    
    def _get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    def add_memory(self, memory: Memory) -> Memory:
        """Add a new memory to storage."""
        session = self._get_session()
        try:
            record = MemoryRecord(
                id=memory.id,
                user_id=memory.user_id,
                agent_id=memory.agent_id,
                memory_type=memory.memory_type.value,
                content=memory.content,
                meta_data=memory.metadata,
                importance=memory.importance,
                timestamp=memory.timestamp,
                last_accessed=memory.last_accessed,
                access_count=memory.access_count,
                tags=memory.tags,
                expires_at=memory.expires_at,
            )
            session.add(record)
            session.commit()
            return memory
        except Exception as e:
            session.rollback()
            raise MemoryStorageError(f"Failed to add memory: {str(e)}", e)
        finally:
            session.close()
    
    def get_memory(self, memory_id: Union[str, UUID]) -> Memory:
        """Get a memory by ID."""
        session = self._get_session()
        try:
            if isinstance(memory_id, str):
                memory_id = UUID(memory_id)
            
            record = session.query(MemoryRecord).filter(MemoryRecord.id == memory_id).first()
            if not record:
                raise MemoryNotFoundError(str(memory_id))
            
            # Update access statistics
            record.last_accessed = datetime.utcnow()
            record.access_count += 1
            session.commit()
            
            # Return the updated memory
            return record.to_memory()
        except MemoryNotFoundError:
            raise
        except Exception as e:
            session.rollback()
            raise MemoryStorageError(f"Failed to get memory: {str(e)}", e)
        finally:
            session.close()
    
    def update_memory(self, memory_id: Union[str, UUID], update: MemoryUpdate) -> Memory:
        """Update a memory."""
        session = self._get_session()
        try:
            if isinstance(memory_id, str):
                memory_id = UUID(memory_id)
            
            record = session.query(MemoryRecord).filter(MemoryRecord.id == memory_id).first()
            if not record:
                raise MemoryNotFoundError(str(memory_id))
            
            # Update fields that are provided
            update_dict = update.model_dump(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(record, field, value)
            
            session.commit()
            return record.to_memory()
        except MemoryNotFoundError:
            raise
        except Exception as e:
            session.rollback()
            raise MemoryStorageError(f"Failed to update memory: {str(e)}", e)
        finally:
            session.close()
    
    def delete_memory(self, memory_id: Union[str, UUID]) -> bool:
        """Delete a memory by ID."""
        session = self._get_session()
        try:
            if isinstance(memory_id, str):
                memory_id = UUID(memory_id)
            
            record = session.query(MemoryRecord).filter(MemoryRecord.id == memory_id).first()
            if not record:
                return False
            
            session.delete(record)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise MemoryStorageError(f"Failed to delete memory: {str(e)}", e)
        finally:
            session.close()
    
    def search_memories(self, query: MemoryQuery) -> List[Memory]:
        """Search memories based on query parameters."""
        session = self._get_session()
        try:
            q = session.query(MemoryRecord)
            
            # Apply filters
            if query.user_id:
                q = q.filter(MemoryRecord.user_id == query.user_id)
            
            if query.agent_id:
                q = q.filter(MemoryRecord.agent_id == query.agent_id)
            
            if query.memory_type:
                q = q.filter(MemoryRecord.memory_type == query.memory_type.value)
            
            if query.content_search:
                q = q.filter(MemoryRecord.content.contains(query.content_search))
            
            if query.min_importance is not None:
                q = q.filter(MemoryRecord.importance >= query.min_importance)
            
            if query.max_importance is not None:
                q = q.filter(MemoryRecord.importance <= query.max_importance)
            
            if query.created_after:
                q = q.filter(MemoryRecord.timestamp >= query.created_after)
            
            if query.created_before:
                q = q.filter(MemoryRecord.timestamp <= query.created_before)
            
            if query.tags:
                # Search for memories that have any of the specified tags
                tag_filters = []
                for tag in query.tags:
                    # Use JSON_CONTAINS or similar functionality for tag matching
                    tag_filters.append(MemoryRecord.tags.contains(tag))
                q = q.filter(or_(*tag_filters))
            
            # Filter out expired memories unless requested
            if not query.include_expired:
                q = q.filter(
                    or_(
                        MemoryRecord.expires_at.is_(None),
                        MemoryRecord.expires_at > datetime.utcnow()
                    )
                )
            
            # Order by importance and timestamp
            q = q.order_by(desc(MemoryRecord.importance), desc(MemoryRecord.timestamp))
            
            # Apply pagination
            q = q.offset(query.offset).limit(query.limit)
            
            records = q.all()
            return [record.to_memory() for record in records]
        except Exception as e:
            raise MemoryStorageError(f"Failed to search memories: {str(e)}", e)
        finally:
            session.close()
    
    def get_user_memories(self, user_id: str, limit: int = 50) -> List[Memory]:
        """Get all memories for a specific user."""
        query = MemoryQuery(user_id=user_id, limit=limit)
        return self.search_memories(query)
    
    def cleanup_expired_memories(self) -> int:
        """Remove expired memories from storage."""
        session = self._get_session()
        try:
            count = session.query(MemoryRecord).filter(
                and_(
                    MemoryRecord.expires_at.isnot(None),
                    MemoryRecord.expires_at <= datetime.utcnow()
                )
            ).delete()
            session.commit()
            return count
        except Exception as e:
            session.rollback()
            raise MemoryStorageError(f"Failed to cleanup expired memories: {str(e)}", e)
        finally:
            session.close() 