"""
Agent Memory - A memory management system for AI agents.

This package provides a simple and efficient way to store and retrieve
user interactions and agent memories for conversational AI applications.
"""

from .core import AgentMemory
from .models import Memory, MemoryType
from .storage import MemoryStorage
from .exceptions import MemoryError, MemoryNotFoundError

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

__all__ = [
    "AgentMemory",
    "Memory",
    "MemoryType", 
    "MemoryStorage",
    "MemoryError",
    "MemoryNotFoundError",
] 