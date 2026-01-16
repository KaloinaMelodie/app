import asyncio
from typing import Any, Dict

from google import genai
from google.genai.types import GenerateContentConfig
from .base import BaseLLMProvider
import os


class GeminiProvider(BaseLLMProvider):
    def __init__(
        self,
        model: str = "gemini-2.5-pro",        # ou "gemini-2.5-flash"
        project: str = os.getenv("GCP_PROJECT_ID"),
        location: str = "us-central1",
    ):
        self.model = model
        if not project:
            raise ValueError("L'environnement GCP_PROJECT_ID est requis pour Vertex mode.")

      
        self.client = genai.Client(
            vertexai=True,
            project=project,
            location=location,
        )

    def name(self) -> str:
        return "vertex-gemini"

    async def generate(self, prompt: str, **kwargs) -> str:
        # Paramètres classiques
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 5000)

        # Optionnel : budget de pensée (si supporté par ton SDK + modèle)
        thinking_budget = kwargs.get("thinking_budget", None)

        def _call() -> str:
            cfg_kwargs: Dict[str, Any] = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }

            if thinking_budget is not None:
                try:
                    from google.genai.types import ThinkingConfig
                    cfg_kwargs["thinking_config"] = ThinkingConfig(
                        thinking_budget=thinking_budget
                    )
                except Exception:
                    pass

            resp = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=GenerateContentConfig(**cfg_kwargs),
            )

            # Extraction robuste du texte
            if getattr(resp, "text", None):
                return resp.text.strip()

            for c in getattr(resp, "candidates", []) or []:
                content = getattr(c, "content", None)
                parts = getattr(content, "parts", None) if content else None
                if parts:
                    texts = [getattr(p, "text", "") for p in parts if getattr(p, "text", None)]
                    if texts:
                        return "".join(texts).strip()

            finish = None
            usage = getattr(resp, "usage_metadata", None)
            if getattr(resp, "candidates", None):
                finish = getattr(resp.candidates[0], "finish_reason", None)
            raise RuntimeError(f"Gemini returned no text. finish_reason={finish}, usage={usage}")

        return await asyncio.to_thread(_call)
