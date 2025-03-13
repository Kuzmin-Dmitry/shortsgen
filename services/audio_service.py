import os
import base64
from config import OPENAI_API_KEY, OPENAI_MODEL, AUDIO_CONFIG, SYSTEM_PROMPT, ASSISTANT_MESSAGE, USER_PROMPT, TEST_AUDIO
from openai import OpenAI

class AudioService:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL
        self.test_mode = TEST_AUDIO

    def generate_audio(self, text, output_path, language='ru', system_prompt=SYSTEM_PROMPT, user_prompt=USER_PROMPT, assistant_message=ASSISTANT_MESSAGE):
        """
        Generates audio with TEST_AUDIO mode support.
        """
        try:
            # Bypass generation if in test mode and file exists
            if self.test_mode and os.path.exists(output_path):
                print(f"Using existing audio: {output_path} [TEST_MODE]")
                return True
                
            print("Generating audio track using GPT‑4o‑audio‑preview...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                modalities=["text", "audio"],
                audio=AUDIO_CONFIG,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt.format(text=text)},
                    {"role": "assistant", "content": assistant_message}
                ]
            )
            
            audio_base64 = response.choices[0].message.audio.data
            audio_bytes = base64.b64decode(audio_base64)
            
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
                
            print(f"Audio file saved: {output_path}")
            return True
            
        except Exception as e:
            print(f"Audio generation error: {e}")
            return False