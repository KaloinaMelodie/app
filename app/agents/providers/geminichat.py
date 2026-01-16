import asyncio
from typing import Any, Dict, List, Optional

from google import genai
from app.utils.langue import detect_dominant_lang
from app.utils.tokens import *
from app.exceptions.exceptions import ValueControlException
from google.genai.types import GenerateContentConfig
import os
import logging

from app.prompt.prompt import SYSTEM_INSTRUCTION, SYSTEM_TRAINING_INSTRUCTION
from app.prompt import PromptFactory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

_LANG_NAME = {
    "fr": "français",
    "en": "anglais",
    "mg": "malagasy",
}
def _lang_name(code: str) -> str:
    return _LANG_NAME.get(code, code)

SimpleMsg = Dict[str, str]  # role,content
 
def _to_genai_message(msg: SimpleMsg) -> Dict[str, Any]:
    role_map = {"user": "user", "assistant": "model"}  
    role = role_map.get(msg["role"], msg["role"])
    return {"role": role, "parts": [{"text": msg["content"]}]}

def _prune_by_count(contents: List[Dict[str, Any]], max_messages: Optional[int]) -> List[Dict[str, Any]]:
    if max_messages is None or len(contents) <= max_messages:
        return contents
    return contents[-max_messages:]

def _prune_by_tokens(
    contents: List[Dict[str, Any]],
    max_tokens_ctx: Optional[int],
    *,
    garde_last_n: int = 2,  
) -> List[Dict[str, Any]]:
    if not max_tokens_ctx:
        return contents
    total = count_contents_tokens(contents)
    if total <= max_tokens_ctx:
        return contents
    pruned = list(contents)
    min_len = min(len(pruned), garde_last_n)
    while len(pruned) > min_len and count_contents_tokens(pruned) > max_tokens_ctx:
        pruned.pop(0)  
    return pruned

class GeminiChatStateless:
    """
    Vertex, stateless
    - Le 'system' va dans GenerateContentConfig.system_instruction (jamais dans contents).
    """
    def __init__(
        self,
        model: str = "gemini-2.5-pro",
        project: str = os.getenv("GCP_PROJECT_ID"),
        location: str = "us-central1",
    ):
        if not project:
            raise ValueControlException("GCP_PROJECT_ID requis.")
        self.model = model
        self.client = genai.Client(vertexai=True, project=project, location=location)

    async def chat(
        self,
        messages: List[SimpleMsg],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        max_messages: Optional[int] = 50,
    ) -> str:
        """Chat simple (sans RAG). Historique."""
        def _call() -> str:
            system_instruction_content: Optional[str] = None
            filtered_msgs: List[SimpleMsg] = []
            for m in messages:
                if m["role"] == "system" and system_instruction_content is None:
                    system_instruction_content = m["content"]
                else:
                    filtered_msgs.append(m)

            contents = [_to_genai_message(m) for m in filtered_msgs]
            contents = _prune_by_count(contents, max_messages=max_messages)

            cfg_kwargs: Dict[str, Any] = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            if system_instruction_content:
                cfg_kwargs["system_instruction"] = {"parts": [{"text": system_instruction_content}]}

            cfg = GenerateContentConfig(**cfg_kwargs)

            resp = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=cfg,
            )
            text = self._extract_text(resp)
            if not text:
                finish = None
                usage = getattr(resp, "usage_metadata", None)
                candidates = getattr(resp, "candidates", None)
                if candidates:
                    finish = getattr(candidates[0], "finish_reason", None)
                raise RuntimeError(f"Gemini returned no text. finish_reason={finish}, usage={usage}")
            return text

        return await asyncio.to_thread(_call)

    async def chat_with_rag_search(
        self,
        messages: List[SimpleMsg],           # historique 
        user_question: str,                  
        search_results: List[Dict[str, Any]],
        *,
        temperature: float = 0.7,
        max_input_tokens: int = 600,
        max_output_tokens: int = 3000, #2048
        max_history_messages: Optional[int] = 5,
        system_instruction: Optional[str] = None,
        max_items: int = 10,
        max_segments: int = 6, 
    ) -> str:        
        def _call() -> str:
            # langue de réponse 
            lang_code, conf = detect_dominant_lang(user_question)
            answer_lang = lang_code if lang_code != "und" else "fr"

            # System instruction
            sys_instr = (system_instruction or
                         _extract_last_system(messages) or
                         SYSTEM_INSTRUCTION)
            
            sys_with_lang = (
                sys_instr
                + f"\n- Réponds dans la langue suivante : {_lang_name(answer_lang)} "
            )

            # conversion historique, ignore system
            contents: List[Dict[str, Any]] = []
            for m in messages or []:
                if m["role"] == "system":
                    continue
                contents.append(_to_genai_message(m))

            # Construction du message user
            packed = PromptFactory.pack_results_for_prompt(
                search_results,
                max_items=max_items,
            )
            user_prompt = PromptFactory.build_user_prompt(user_question=user_question, packed_results_json=packed)
            contents.append({"role": "user", "parts": [{"text": user_prompt}]})

            # Tronque historique
            contents = _prune_by_count(contents, max_messages=max_history_messages)

            contents = _prune_by_tokens(
                contents,
                max_tokens_ctx=max_input_tokens,
                garde_last_n=2
            )

            logger.info(contents)

            # Appel modèle, avec sys_with_lang
            cfg = GenerateContentConfig(
                temperature=temperature,
                # max_output_tokens=max_output_tokens,
                candidate_count=2,
                system_instruction={"parts": [{"text": sys_with_lang}]},
            )
            resp = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=cfg,
            )
            text = self._extract_text(resp)
            if not text:
                finish = None
                usage = getattr(resp, "usage_metadata", None)
                candidates = getattr(resp, "candidates", None)
                if candidates:
                    finish = getattr(candidates[0], "finish_reason", None)
                raise RuntimeError(f"Gemini returned no text. finish_reason={finish}, usage={usage}")
            return text

        return await asyncio.to_thread(_call)
    
    async def chat_with_rag_training(
        self,
        messages: List[SimpleMsg],           # historique 
        user_question: str,                  
        search_results: List[Dict[str, Any]],
        *,
        temperature: float = 0.7,
        max_input_tokens: int = 3000, #2000-3000 
        max_output_tokens: int = 3000, #2048
        max_history_messages: Optional[int] = 5,
        system_instruction: Optional[str] = None,
        max_items: int = 10,
    ) -> str:        
        def _call() -> str:
            # langue de réponse 
            lang_code, conf = detect_dominant_lang(user_question)
            answer_lang = lang_code if lang_code != "und" else "fr"

            # System instruction
            sys_instr = (system_instruction or
                         _extract_last_system(messages) or
                         SYSTEM_TRAINING_INSTRUCTION)
            
            sys_with_lang = (
                sys_instr
                + f"\n- Réponds dans la langue suivante : {_lang_name(answer_lang)} "
            )

            # conversion historique, ignore system
            contents: List[Dict[str, Any]] = []
            for m in messages or []:
                if m["role"] == "system":
                    continue
                contents.append(_to_genai_message(m))

            # Construction du message user
            packed = PromptFactory.pack_results_for_prompt(
                search_results,
                max_items=max_items,
            )
            user_training_prompt = PromptFactory.build_user_training_prompt(user_question=user_question, packed_results_json=packed)
            contents.append({"role": "user", "parts": [{"text": user_training_prompt}]})

            # Tronque historique
            contents = _prune_by_count(contents, max_messages=max_history_messages)

            contents = _prune_by_tokens(
                contents,
                max_tokens_ctx=max_input_tokens,
                garde_last_n=2
            )

            # Appel modèle, avec sys_with_lang
            cfg = GenerateContentConfig(
                temperature=temperature,
                # max_output_tokens=max_output_tokens,
                candidate_count=2,
                system_instruction={"parts": [{"text": sys_with_lang}]},
            )
            resp = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=cfg,
            )
            text = self._extract_text(resp)
            if not text:
                finish = None
                usage = getattr(resp, "usage_metadata", None)
                candidates = getattr(resp, "candidates", None)
                if candidates:
                    finish = getattr(candidates[0], "finish_reason", None)
                raise RuntimeError(f"Gemini returned no text. finish_reason={finish}, usage={usage}")
            return text

        return await asyncio.to_thread(_call)

    @staticmethod
    def _extract_text(resp: Any) -> str:
        if getattr(resp, "text", None):
            return resp.text.strip()
        for c in getattr(resp, "candidates", []) or []:
            content = getattr(c, "content", None)
            parts = getattr(content, "parts", None) if content else None
            if parts:
                texts = [getattr(p, "text", "") for p in parts if getattr(p, "text", None)]
                if texts:
                    return "".join(texts).strip()
        return ""

def _extract_last_system(messages: List[SimpleMsg]) -> Optional[str]:
    sys_txt = None
    for m in messages or []:
        if m.get("role") == "system":
            sys_txt = m.get("content")
    return sys_txt
