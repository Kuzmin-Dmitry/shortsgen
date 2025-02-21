"""
Module for generating an audio track with narration using GPT‑4o‑audio‑preview.

This module utilizes OpenAI's GPT‑4o‑audio‑preview model to convert text into vivid,
emotionally charged audio. It sends text instructions to generate an audio file
and saves the resulting MP3 output to a specified path.
"""

import base64
from config import OPENAI_API_KEY, OPENAI_MODEL, AUDIO_CONFIG, SYSTEM_PROMPT, ASSISTANT_MESSAGE, USER_PROMPT
from openai import OpenAI

# Initialize the OpenAI client with the API key.
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_audio(text, output_path, language='ru', model=OPENAI_MODEL, system_promt=SYSTEM_PROMPT, 
                   user_prompt=USER_PROMPT, assistant_message=ASSISTANT_MESSAGE):
    """
    Generates an audio file narrating the provided text.
    
    Parameters:
        text (str): The text to be narrated.
        output_path (str): The file path where the generated audio file will be saved.
        language (str): The language code for narration (currently unused; default is 'ru').
    
    Returns:
        bool: True if the audio was successfully generated and saved, otherwise False.
    """
    try:
        print("Generating audio track using GPT‑4o‑audio‑preview...")
        
        # Send a chat completion request with both text and audio modalities.
        response = client.chat.completions.create(
            model=model,
            modalities=["text", "audio"],
            audio=AUDIO_CONFIG,
            messages=[
                {"role": "system", "content": system_promt},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": assistant_message}
            ]
        )
        
        # Extract the Base64 encoded audio data from the response and decode it.
        audio_base64 = response.choices[0].message.audio.data
        audio_bytes = base64.b64decode(audio_base64)
        
        # Save the decoded audio bytes to the specified file path.
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        
        print(f"Audio file saved: {output_path}")
        return True
    except Exception as e:
        print(f"Audio generation error: {e}")
        return False
