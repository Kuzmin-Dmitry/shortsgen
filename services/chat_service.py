"""
Module for generating text using language models.

This module provides a unified interface for text generation using different
language models including OpenAI's GPT models and local models like Gemma.
"""

from typing import Dict, List, Optional, Any, Union, TypedDict, cast
from enum import Enum
from dataclasses import dataclass
import json
import logging
from openai import OpenAI
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice, ChatCompletionMessage
import requests
from config import OPENAI_API_KEY, LOCAL_TEXT_TO_TEXT_MODEL

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Enum for supported model types."""
    OPENAI = "openai"
    GEMMA = "gemma"

class ResponseFormat(Enum):
    """Enum for response format types."""
    TEXT = "text"
    JSON = "json"
    TOOL_CALLS = "tool_calls"

class ModelException(Exception):
    """Base exception for model-related errors."""
    pass

class OpenAIException(ModelException):
    """Exception for OpenAI-specific errors."""
    pass

class GemmaException(ModelException):
    """Exception for local Gemma model errors."""
    pass

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

class ChatService:
    """
    Service for text generation using different language models.
    
    This service provides a unified interface for generating text using
    either OpenAI's models or local models like Gemma.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the ChatService with optional custom API key.
        
        Args:
            api_key: Optional API key for OpenAI. If None, uses key from config.
        """
        self.api_key = api_key or OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key)
        logger.info("ChatService initialized with OpenAI client")

    def generate_text(
        self, 
        prompt: str, 
        functions: Optional[List[Dict[str, Any]]] = None, 
        max_tokens: int = 300, 
        model: Union[str, ModelType] = ModelType.OPENAI, 
        temperature: float = 0.8
    ) -> Union[str, Dict[str, Any]]:
        """
        Generate text using the specified model.
        
        Args:
            prompt: The text prompt to generate from
            functions: List of function definitions for the model to use
            max_tokens: Maximum number of tokens in the response
            model: Model type to use (ModelType enum or string)
            temperature: Controls randomness in generation (0.0-1.0)
            
        Returns:
            Generated text or structured data from function calls
            
        Raises:
            ModelException: For model-related errors
            ValueError: For invalid parameters
        """
        # Convert string model type to enum if needed
        if isinstance(model, str):
            try:
                model = ModelType(model)
            except ValueError:
                # If string doesn't match enum exactly, try default mapping
                model = ModelType.GEMMA if model.lower() == "gemma" else ModelType.OPENAI
        
        # Log the generation attempt
        prompt_truncated = prompt[:30] + "..." if len(prompt) > 30 else prompt
        logger.info(f"Generating text with model={model.value}, max_tokens={max_tokens}, temperature={temperature}")
        logger.debug(f"Full prompt: {prompt}")
        
        try:
            # Generate based on model type
            if model == ModelType.GEMMA:
                response = self._generate_text_gemma3(prompt, max_tokens, temperature)
            else:
                response = self._generate_text_openai(prompt, functions, max_tokens, temperature)
            
            # Log results
            if isinstance(response.content, str):
                result_length = len(response.content)
                logger.info(f"Text generation completed. Generated {result_length} characters")
                logger.debug(f"Full result: {response.content}")
            
            # Return appropriate content based on tool calls
            if response.has_tool_calls():
                # If we have tool calls, return the parsed arguments from the first call
                # This maintains backward compatibility with the current implementation
                return response.tool_calls[0]['arguments']
            else:
                # Otherwise return the text content
                return response.content
                
        except ModelException as e:
            logger.error(f"Error generating text: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in text generation: {str(e)}")
            raise ModelException(f"Unexpected error: {str(e)}")

    def _generate_text_gemma3(
        self, 
        prompt: str, 
        max_tokens: int = 300, 
        temperature: float = 0.7
    ) -> ModelResponse:
        """
        Generate text using local Gemma model.
        
        Args:
            prompt: The text prompt to generate from
            max_tokens: Maximum number of tokens to generate
            temperature: Controls randomness (0.0-1.0)
            
        Returns:
            ModelResponse containing the generated text
            
        Raises:
            GemmaException: If there's an error with the Gemma model
        """
        logger.debug(f"Request payload: {prompt}, max_tokens={max_tokens}, temperature={temperature}")
        
        try:
            # Prepare the request for local Gemma model
            payload = {
                "model": LOCAL_TEXT_TO_TEXT_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "top_p": 0.9,
                    "num_ctx": 4096
                }
            }
            
            # Send request to local Gemma instance
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload
            )
            
            # Handle the response
            if response.status_code == 200:
                response_json = response.json()
                text_response = response_json.get("response", "")
                logger.debug(f"Gemma response: {response_json}")
                return ModelResponse(content=text_response, raw_response=response_json)
            else:
                error_message = f"Gemma API returned non-200 status code: {response.status_code}"
                logger.warning(error_message)
                raise GemmaException(error_message)
                
        except requests.RequestException as e:
            error_message = f"Error calling local Gemma model: {str(e)}"
            logger.error(error_message)
            raise GemmaException(error_message)
        except Exception as e:
            error_message = f"Unexpected error with Gemma model: {str(e)}"
            logger.error(error_message)
            raise GemmaException(error_message)
    
    def _generate_text_openai(
        self, 
        prompt: str, 
        functions: Optional[List[Dict[str, Any]]] = None, 
        max_tokens: int = 300, 
        temperature: float = 0.8
    ) -> ModelResponse:
        """
        Generate text using OpenAI models.
        
        Args:
            prompt: The text prompt to generate from
            functions: List of function definitions for the model
            max_tokens: Maximum number of tokens to generate
            temperature: Controls randomness (0.0-1.0)
            
        Returns:
            ModelResponse containing the generated text and any tool calls
            
        Raises:
            OpenAIException: If there's an error with the OpenAI API
        """
        try:
            # Create parameters dictionary for OpenAI API
            params = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a comic book writer's assistant, ready to help create a unique plot."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            # Add functions if provided
            if functions is not None:
                params["tools"] = functions
                params["tool_choice"] = "auto"
            
            logger.debug(f"OpenAI request parameters: {params}")
            
            # Call OpenAI API
            response = self.client.chat.completions.create(**params)
            logger.debug(f"OpenAI response: {response}")
            
            # Extract the message from the response
            message = response.choices[0].message
            
            # Process tool calls if present
            tool_calls: Optional[List[FunctionCall]] = None
            if hasattr(message, 'tool_calls') and message.tool_calls:
                tool_calls = []
                for tool_call in message.tool_calls:
                    if tool_call.type == "function":
                        # Parse function arguments
                        try:
                            arguments = json.loads(tool_call.function.arguments)
                            tool_calls.append({
                                "name": tool_call.function.name,
                                "arguments": arguments
                            })
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse function arguments: {e}")
            
            # Return structured response
            return ModelResponse(
                content=message.content or "",
                tool_calls=tool_calls,
                raw_response=response
            )
            
        except Exception as e:
            error_message = f"Error calling OpenAI API: {str(e)}"
            logger.error(error_message)
            raise OpenAIException(error_message)

    def extract_queries_from_tool_call(self, tool_call_result: Dict[str, Any]) -> List[str]:
        """
        Extract search queries from tool call result.
        
        Args:
            tool_call_result: Dictionary with tool call results
            
        Returns:
            List of search queries
        """
        # Handle 'queries' field directly
        if "queries" in tool_call_result:
            return tool_call_result["queries"]
        
        # Handle legacy 'scenes' format
        if "scenes" in tool_call_result and isinstance(tool_call_result["scenes"], list):
            return [scene.get("query", "") for scene in tool_call_result["scenes"]]
        
        # Return empty list if neither format is found
        return []
