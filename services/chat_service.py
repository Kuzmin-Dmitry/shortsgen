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
        logger.debug("Initializing text generation class")  # Отладочное сообщение при инициализации класса
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        logger.debug("Closed text generation class initialized")

    def generate_text(self, prompt, max_tokens=300, model=None, temperature=0.8):
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
        logger.info(f"Generating text using prompt: {prompt[:40] + '...'}")
        
        if model == "gemma" or (model is None):
            return self._generate_chatgpt_text_gemma3(prompt, max_tokens, temperature)
        else:
            return self._generate_chatgpt_text_openai(prompt, max_tokens, temperature)

    def _generate_chatgpt_text_gemma3(self, prompt, max_tokens=300, temperature=0.7):
        """Private method for generating text using local Gemma model."""
        logger.info(f"Sending request to local Gemma model: {prompt[:40] + '...'}")
        
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
            logger.info(f"Received response from Gemma: {text_response[:40] + '...' if text_response else 'Empty response'}")
            return text_response
        else:
            logger.error(f"Error from Gemma API: {response.status_code} - {response.text}")
            return ""
    
    def _generate_chatgpt_text_openai(self, prompt, max_tokens=300, temperature=0.8):
        """
        Private method for generating text using OpenAI models.
        Returns the generated text as a string.
        """
        logger.info(f"Sending request to ChatGPT: {prompt[:40] + '...'}")
        
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
        logger.info(f"Received response from ChatGPT: {text_response[:40] + '...' if text_response else 'Empty response'}")
        
        return text_response
