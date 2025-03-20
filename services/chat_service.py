"""
Module for generating text using the ChatGPT API.
"""

from openai import OpenAI
from config import OPENAI_API_KEY, LOCAL_TEXT_TO_TEXT_MODEL
import requests

class ChatService:   
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)



    def generate_chatgpt_text_gemma3(self, prompt, max_tokens=300):
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": LOCAL_TEXT_TO_TEXT_MODEL,
                "prompt": prompt,
                "stream": False,  # Set to True for streaming response
                "options": {
                    "temperature": 0.7,
                    "max_tokens": max_tokens,
                    "top_p": 0.9,
                    "num_ctx": 4096  # Context window size
                }
            }
        )
        print(response.json()["response"]) 
        return response.json()["response"]
    
    def generate_chatgpt_text_openai(self, prompt, max_tokens=300):
        """
        Generates text response using the ChatGPT API based on the provided prompt.
        Returns a list containing the generated texts.
        """
        print(f"Sending request to ChatGPT: {prompt}")  # Log the outgoing prompt.
        # Request a text completion from ChatGPT.
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",  # The model identifier can be customized as needed.
            messages=[
                {"role": "system", "content": "You are a comic book writer's assistant, ready to help create a unique plot."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.8  # Adjust temperature to control the creativity of the output.
        )
        # Clean and store the generated text.
        response = response.choices[0].message.content.strip()
        print("Received response from ChatGPT.")  # Confirm that response have been collected.
        return response
