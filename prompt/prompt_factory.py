from typing import List, Dict
from .navigation_prompt import NAVIGATION_PROMPT


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
