"""
Module for generating text using the ChatGPT API.
"""

from openai import OpenAI
from config import OPENAI_API_KEY, LOCAL_TEXT_TO_TEXT_MODEL
import logging
import requests

logger = logging.getLogger(__name__)

class ChatService:   
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("ChatService initialized with OpenAI client")

    def generate_text(self, prompt, max_tokens=300, model="openai", temperature=0.8):
        """
        Unified interface for text generation using different models.
        
        Args:
            prompt (str): The text prompt to generate from
            max_tokens (int): Maximum number of tokens in the response
            model (str, optional): Model to use. If None, will use local or OpenAI based on config
            temperature (float): Controls randomness in generation (0.0-1.0)
            
        Returns:
            str: Generated text
        """
        prompt_truncated = prompt[:30] + "..." if len(prompt) > 30 else prompt
        logger.info(f"Generating text with model={model or 'default'}, max_tokens={max_tokens}, temperature={temperature}")
        logger.debug(f"Prompt: {prompt_truncated}")
        
        try:
            if model == "gemma":
                result = self._generate_chatgpt_text_gemma3(prompt, max_tokens, temperature)
            else:
                result = self._generate_chatgpt_text_openai(prompt, max_tokens, temperature)
                
            result_length = len(result)
            logger.info(f"Text generation completed. Generated {result_length} characters")
            logger.debug(f"Result preview: {result[:30]}..." if result_length > 30 else result)
            return result
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            raise

    def _generate_chatgpt_text_gemma3(self, prompt, max_tokens=300, temperature=0.7):
        """Private method for generating text using local Gemma model."""
        logger.debug(f"Using local Gemma model with temperature={temperature}, max_tokens={max_tokens}")
        
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
                logger.debug(f"Received successful response from Gemma model")
                return text_response
            else:
                logger.warning(f"Gemma API returned non-200 status code: {response.status_code}")
                return ""
        except Exception as e:
            logger.error(f"Error calling local Gemma model: {str(e)}")
            raise
    
    def _generate_chatgpt_text_openai(self, prompt, max_tokens=300, temperature=0.8):
        """
        Private method for generating text using OpenAI models.
        Returns the generated text as a string.
        """
        logger.debug(f"Using OpenAI model with temperature={temperature}, max_tokens={max_tokens}")
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a comic book writer's assistant, ready to help create a unique plot."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            text_response = response.choices[0].message.content.strip()
            logger.debug(f"Received successful response from OpenAI model")
            
            return text_response
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            raise
