"""
Module for generating text using the ChatGPT API.
"""

from openai import OpenAI
from config import OPENAI_API_KEY, LOCAL_TEXT_TO_TEXT_MODEL, SEARCH_QUERY_FUNCTION
import logging
import requests

logger = logging.getLogger(__name__)

class ChatService:   
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("ChatService initialized with OpenAI client")

    def generate_text(self, prompt, functions=None, max_tokens=300, model="openai", temperature=0.8):
        """
        Unified interface for text generation using different models.
        
        Args:
            prompt (str): The text prompt to generate from
            functions (list, optional): List of function definitions for the model to use
            max_tokens (int): Maximum number of tokens in the response
            model (str, optional): Model to use. If None, will use local or OpenAI based on config
            temperature (float): Controls randomness in generation (0.0-1.0)
            
        Returns:
            str: Generated text
        """
        prompt_truncated = prompt[:30] + "..." if len(prompt) > 30 else prompt
        logger.info(f"Generating text with model={model or 'default'}, max_tokens={max_tokens}, temperature={temperature}")
        logger.debug(f"Full prompt: {prompt}")
        
        try:
            if model == "gemma":
                result = self._generate_text_gemma3(prompt, max_tokens, temperature)
            else:
                result = self._generate_text_openai(prompt, functions, max_tokens, temperature)
                
            result_length = len(result)
            logger.info(f"Text generation completed. Generated {result_length} characters")
            logger.debug(f"Full result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            raise

    def _generate_text_gemma3(self, prompt, max_tokens=300, temperature=0.7):
        """Private method for generating text using local Gemma model."""
        logger.debug(f"Request payload: {prompt}, max_tokens={max_tokens}, temperature={temperature}")
        
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
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
            )
            
            if response.status_code == 200:
                text_response = response.json().get("response", "")
                logger.debug(f"Gemma response: {response.json()}")
                return text_response
            else:
                logger.warning(f"Gemma API returned non-200 status code: {response.status_code}")
                return ""
        except Exception as e:
            logger.error(f"Error calling local Gemma model: {str(e)}")
            raise
    
    def _generate_text_openai(self, prompt, functions=None, max_tokens=300, temperature=0.8):
        """
        Private method for generating text using OpenAI models.
        Returns the generated text as a string.
        """
        try:
            # Create a parameters dictionary
            params = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a comic book writer's assistant, ready to help create a unique plot."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            # Only add functions if they are provided
            if functions is not None:
                params["tools"] = functions
                params["tool_choice"] = "auto"
            logger.debug(f"OpenAI request parameters: {params}")
            
            response = self.client.chat.completions.create(**params)
            logger.debug(f"OpenAI response: {response}")
            
            # Check if response has tool calls or regular content
            if hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
                # Extract the function call results
                tool_call = response.choices[0].message.tool_calls[0]
                if tool_call.type == "function":
                    import json
                    function_args = json.loads(tool_call.function.arguments)
                    logger.debug(f"Function call returned: {function_args}")
                    
                    # Упрощенная обработка - просто возвращаем queries если они есть
                    if "queries" in function_args:
                        return function_args["queries"]
                    
                    # Для обратной совместимости
                    if "scenes" in function_args and isinstance(function_args["scenes"], list):
                        return [scene.get("query", "") for scene in function_args["scenes"]]
                    
                    return function_args
            
            # If no tool calls, return the regular content
            text_response = response.choices[0].message.content.strip()
            logger.debug(f"Received successful response from OpenAI model")
            
            return text_response
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            raise
