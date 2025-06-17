"""Base exceptions for text generation service."""

class ModelException(Exception):
    """Base exception for model-related errors."""
    pass

class OpenAIException(ModelException):
    """Exception for OpenAI-specific errors."""
    pass

class GemmaException(ModelException):
    """Exception for local Gemma model errors."""
    pass
