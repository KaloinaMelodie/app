from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        pass

    @abstractmethod
    def name(self) -> str:
        pass
