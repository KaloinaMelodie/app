from .providers.base import BaseLLMProvider

class LLMManager:
    def __init__(self, providers: list[BaseLLMProvider]):
        self.providers = {provider.name(): provider for provider in providers}

    def get_provider(self, name: str) -> BaseLLMProvider:
        if name not in self.providers:
            raise ValueError(f"Provider '{name}' non reconnu.")
        return self.providers[name]

    async def generate(self, prompt: str, provider_name: str, **kwargs) -> str:
        provider = self.get_provider(provider_name)
        return await provider.generate(prompt, **kwargs)
