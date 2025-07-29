"""Custom exceptions for the agent memory system."""


class MemoryError(Exception):
    """Base exception for all memory-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class MemoryNotFoundError(MemoryError):
    """Raised when a requested memory cannot be found."""
    
    def __init__(self, memory_id: str, details: dict = None):
        message = f"Memory with ID '{memory_id}' not found"
        super().__init__(message, details)
        self.memory_id = memory_id


class MemoryStorageError(MemoryError):
    """Raised when there's an error with the storage backend."""
    
    def __init__(self, message: str, original_error: Exception = None, details: dict = None):
        super().__init__(message, details)
        self.original_error = original_error


class MemoryValidationError(MemoryError):
    """Raised when memory data fails validation."""
    
    def __init__(self, message: str, field: str = None, details: dict = None):
        super().__init__(message, details)
        self.field = field


class MemoryPermissionError(MemoryError):
    """Raised when user doesn't have permission to access a memory."""
    
    def __init__(self, memory_id: str, user_id: str, details: dict = None):
        message = f"User '{user_id}' does not have permission to access memory '{memory_id}'"
        super().__init__(message, details)
        self.memory_id = memory_id
        self.user_id = user_id 