import os
import base64
from config import OPENAI_API_KEY, OPENAI_MODEL, AUDIO_CONFIG, SYSTEM_PROMPT, ASSISTANT_MESSAGE, USER_PROMPT, TEST_AUDIO
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

class AudioService:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL
        self.test_mode = TEST_AUDIO
        logger.info(f"AudioService initialized with model={self.model}, test_mode={self.test_mode}")

    def generate_audio(self, text, output_path, language='ru', system_prompt=SYSTEM_PROMPT, user_prompt=USER_PROMPT, assistant_message=ASSISTANT_MESSAGE):
        """
        Generates audio with TEST_AUDIO mode support.
        """
        try:
            # Log input parameters
            text_preview = text[:30] + "..." if len(text) > 30 else text
            logger.info(f"Generating audio to {output_path}, language={language}")
            logger.debug(f"Text to synthesize: {text_preview}")
            
            # Bypass generation if in test mode and file exists
            if self.test_mode and os.path.exists(output_path):
                logger.info(f"Using existing audio: {output_path} [TEST_MODE]")
                return True
                
            logger.info(f"Generating audio track using model: {self.model}")
            
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
            
            logger.debug("Audio generation completed, processing response")
            audio_base64 = response.choices[0].message.audio.data
            audio_bytes = base64.b64decode(audio_base64)
            
            # Save the file
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            
            file_size = os.path.getsize(output_path) / 1024  # Size in KB
            logger.info(f"Audio file saved: {output_path} ({file_size:.2f} KB)")
            return True
            
        except Exception as e:
            logger.error(f"Audio generation error: {str(e)}", exc_info=True)
            return False