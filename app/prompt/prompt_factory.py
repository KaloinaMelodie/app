from __future__ import annotations
import json
from textwrap import shorten
from typing import Any, List, Dict
from .navigation_prompt import NAVIGATION_PROMPT
from .prompt import USER_PROMPT, USER_TRAINING_PROMPT


class PromptFactory:
    @staticmethod
    def get_navigation_prompt(user_question: str, search_results: List[Dict]) -> str:
        formatted_results = PromptFactory.format_results(search_results)
        return NAVIGATION_PROMPT.format(
            user_question=user_question.strip(),
            search_results=formatted_results
        )

    @staticmethod
    def format_results(results: List[Dict]) -> str:
        if not results:
            return "Aucun document pertinent n'a été trouvé."

        output = []
        for i, item in enumerate(results, start=1):
            nom = item.get("nom", "[Nom inconnu]")
            emplacement = item.get("emplacement", "[Emplacement manquant]")
            contenu = item.get("contenu", "").strip()
            output.append(
                f"{i}. **Nom** : {nom}\n   **Emplacement** : {emplacement}\n   **Contenu extrait** : {contenu}"
            )
        return "\n\n".join(output)

    @staticmethod
    def build_user_prompt(user_question: str, packed_results_json: str) -> str:
        return USER_PROMPT.format(
                user_question=user_question.strip(),
                search_results=packed_results_json
            )

    @staticmethod
    def build_user_training_prompt(user_question: str, packed_results_json: str) -> str:
        return USER_TRAINING_PROMPT.format(
                user_question=user_question.strip(),
                search_results=packed_results_json
            )

    @staticmethod    
    def pack_results_for_prompt(
        results: List[Dict[str, Any]],
        *,
        max_items: int = 10,
        max_chars_per_content: int = 1200,
    ) -> str:
        safe = []
        for r in (results or [])[:max_items]:
            item = {
                "nom": r.get("nom") or "",
                "emplacement": r.get("emplacement") or [],
                # "content": shorten(str(r.get("content") or "").strip(),
                #                    width=max_chars_per_content,
                #                    placeholder="…")
                "content": str(r.get("content") or "").strip()
            }
            if "score" in r: 
                try: 
                    item["score"] = float(r["score"])
                except Exception: 
                    pass
            safe.append(item)
        return json.dumps(safe, ensure_ascii=False, indent=2)

