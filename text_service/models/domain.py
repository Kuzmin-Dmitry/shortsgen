"""Domain models for text generation service."""

from typing import Dict, List, Optional, Any, TypedDict
from enum import Enum
from dataclasses import dataclass

class ModelType(Enum):
    """Enum for supported model types."""
    OPENAI = "openai"
    GEMMA = "gemma"

class ResponseFormat(Enum):
    """Enum for response format types."""
    TEXT = "text"
    JSON = "json"
    TOOL_CALLS = "tool_calls"

class FunctionCall(TypedDict):
    """Type for function call results."""
    name: str
    arguments: Dict[str, Any]

@dataclass
class ModelResponse:
    """Structured response from model generation."""
    content: str
    tool_calls: Optional[List[FunctionCall]] = None
    raw_response: Optional[Any] = None
    
    def has_tool_calls(self) -> bool:
        """Check if response contains tool calls."""
        return self.tool_calls is not None and len(self.tool_calls) > 0
