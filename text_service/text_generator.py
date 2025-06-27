"""
OpenAI Text Generation Service
"""

from openai import AsyncOpenAI
from typing import Optional
from config import OPENAI_API_KEY, logger


class GetTextOpenAI:
    """OpenAI API клиент для генерации текста"""
    
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY не установлен")
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)

    async def generate_text(
        self, 
        prompt: str,
        model: str = "o4-mini",
        tone: str = "neutral",
        language: str = "ru", 
        max_tokens: int = 256
    ) -> str:
        """Генерирует текст используя OpenAI API"""
        
        system_prompt = f"""Создай текст на языке: {language}, тон: {tone}.
        Максимум токенов: {max_tokens}. Будь лаконичен и креативен."""
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            generated_text = response.choices[0].message.content or ""
            generated_text = generated_text.strip()
            logger.info(f"Generated text: {len(generated_text)} characters")
            return generated_text
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
