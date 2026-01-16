from openai import AsyncOpenAI
from app.core import settings
from .base import BaseLLMProvider
class OpenRouterProvider(BaseLLMProvider):
    def __init__(self, model: str, api_key: str):
        self.client = AsyncOpenAI(
            base_url=settings.openrouter_baseurl,
            api_key=settings.openrouter_apikey
        )
        self.model = model

    def name(self):
        return "openrouter"

    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", 0.7)
        )
        return response.choices[0].message.content.strip()
