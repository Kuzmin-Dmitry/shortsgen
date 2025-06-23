import openai
from config import OPENAI_API_KEY, DEFAULT_OPENAI_MODEL
from models import TextGenerationRequest, TextGenerationResponse

class OpenAIService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    def generate_text(self, request: TextGenerationRequest) -> TextGenerationResponse:
        try:
            response = self.client.chat.completions.create(
                model=DEFAULT_OPENAI_MODEL,
                messages=[{"role": "user", "content": request.prompt}],
                max_tokens=request.max_tokens or 300,
                temperature=request.temperature or 0.8
            )
            
            content = response.choices[0].message.content
            generated_text = content.strip() if content else ""
            
            return TextGenerationResponse(
                success=True,
                content=generated_text,
                message="Text generated successfully",
                model_used=DEFAULT_OPENAI_MODEL,
                tokens_generated=response.usage.completion_tokens if response.usage else 0
            )
        except Exception as e:
            return TextGenerationResponse(
                success=False,
                content="",
                message=str(e),
                model_used="",
                tokens_generated=0
            )

_service = None

def get_openai_service():
    global _service
    if _service is None:
        _service = OpenAIService()
    return _service