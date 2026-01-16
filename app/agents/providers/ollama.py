from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from .base import BaseLLMProvider
from app.core import settings

class OllamaProvider(BaseLLMProvider):
    def __init__(self, model: str = "llama3.2", host: str = settings.ollama_host, port: int = settings.ollama_port):
        self.model = model
        self.base_url = f"https://{host}:{port}"
        self.llm = ChatOllama(model=model, base_url=self.base_url)

    def name(self):
        return "ollama"

    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content