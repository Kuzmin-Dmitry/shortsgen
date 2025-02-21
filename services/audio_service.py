"""
Module for generating an audio track with narration using GPT‑4o‑audio‑preview.

This module utilizes OpenAI's GPT‑4o‑audio‑preview model to convert text into vivid,
emotionally charged audio. It sends text instructions to generate an audio file
and saves the resulting MP3 output to a specified path.
"""

import base64
from config import OPENAI_API_KEY
from openai import OpenAI

# Initialize the OpenAI client with the API key.
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_audio(text, output_path, language='ru'):
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
        
        # Define the system prompt that sets the narration style and characteristics.
        system_message = (
            "You are a highly skilled audio assistant capable of transforming text into vivid, emotionally charged audio. "
            "Maintain a voice pitch between 180–230 Hz and a dynamic range that spans from a soft whisper to powerful delivery, "
            "allowing for expressive emotional bursts. "
            "Adopt a resonant tone with a slight huskiness and sarcastic nuances; minimal jitter and shimmer ensure sound stability. "
            "Speak with clear diction, incorporating expressive intonation shifts and pauses that convey confidence and playful mockery. "
            "Instantly adjust your tone from mocking irony to deep expressiveness, reflecting a rich inner world and bold character. "
            "Speak with a clear Russian accent."
        )
        # Create a user message that instructs the assistant to narrate the provided text swiftly and with maximum clarity and emotion.
        user_message = f"Please narrate the following text with maximum clarity and emotion, but quickly: «{text}»"
        # Provide an assistant message that simulates a confirmation response from the audio model.
        assistant_message = "Audio output generated. The transcript of the audio is provided below."
        
        # Send a chat completion request with both text and audio modalities.
        response = client.chat.completions.create(
            model="gpt-4o-audio-preview",
            modalities=["text", "audio"],
            audio={"voice": "nova", "format": "mp3"},
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
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
