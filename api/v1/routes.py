from fastapi import APIRouter, HTTPException, Body,Query
from app.models import SurveyItem,ConsoleItem
from app.models import TextInput,QuestionInput
from app.services.milvus_service import MilvusService
from app.services.hive_service import fetch_consoles_to_create, fetch_some_surveys,fetch_surveys_to_create,fetch_surveys_to_delete
from app.agents.embedder import generate_embedding
from app.exceptions.exceptions import *
from app.core.responses import *
from app.agents import *
from typing import List, Optional
from app.prompt import PromptFactory
import logging
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
router = APIRouter()

llm_manager = LLMManager([
    OllamaProvider(model="llama3.2"),
    # OpenRouterProvider(model="mistralai/mixtral-8x7b", api_key="sk-...")
])

ROOT = Path(__file__).resolve().parents[3] 
LOCALES_DIR = Path(os.getenv("LOCALES_DIR", ROOT / "locales"))


@router.get("/i18n/locales/{lng}/{ns}.json")
def get_locale(lng: str, ns: str):
  path = LOCALES_DIR / lng / f"{ns}.json"
  if not path.exists():
    return JSONResponse({"error": "not found"}, status_code=404)
  return FileResponse(path)


@router.get("/generate")
async def generate(
    input: Optional[QuestionInput] = Body(default = None),
    provider: str = Query("ollama"),
    temperature: float = Query(0.7)
):
    try:
        if input is None:
            raise BadRequestException("Donnée manquant")
        search_results = [
            {        
      "id": "04258211665b474dbe6fd9107fba52d6_0",
      "doc_id": "04258211665b474dbe6fd9107fba52d6",
      "chunk_index": 0,
      "nom": "De SAHI Anosy-MUS formulaire ménage",
      "emplacement": [
        "https://portal.mwater.co/#/forms/04258211665b474dbe6fd9107fba52d6"
      ],
      "content": "De SAHI Anosy-MUS formulaire ménage. Contexte. Site Ménage. Sites liés. Communauté. Dans quelle communauté ce ménage fait-il partie ? Limite administrative. Région. District. Commune. Le commune n'est pas trouvé sur la liste des limites administratives. Quel est le nom du commune ? Milieu de résidence. Urbain. Rural. Fokontany. Date de l'enquête. <**REMARQUE: L'enquêteur doit lire ce texte tel qu’il est rédigé**>. Puis-je commencer maintenant ? Oui. Non. Si OUI, commencer l'entretien, Si non, arrêter l'entretien. **Note:** Le consentement ne peut être obtenu que si la personne interrogée est âgée de 18 ans ou plus. Pour les moins de 18 ans, l'assentiment de la personne interrogée et le consentement du parent ou du tuteur sont nécessaires. Si le consentement/l'assentiment n'est pas obtenu, l'entretien ne doit pas commencer. CARACTERISTIQUES SOCIODEMOGRAPHIQUES ET ECONOMIQUES DES MENAGES. Qui a répondu au questionnaire ? Chef de ménage. Le ou la Conjoint(e). Other (please specify). CARACTERISTIQUES SOCIODEMOGRAPHIQUES ET ECONOMIQUES DES INDIVIDUS. Tout d'abord, dites-moi SVP le nom de chaque personne qui vit habituellement ici, en commençant par le chef de ménage. Quel est le lien de parenté de (nom) avec (nom du chef de ménage) ? CM. Conjoint (e). Fils/Fille. Other (please specify). Est-ce que (nom) est de sexe masculin ou féminin ? Homme. Femme. Quel âge a (nom) ? Enregistrer en années révolues. Quel est le niveau d’éducation du CM ? Sans niveau. Primaire. Secondaire I. Secondaire II ou plus. Cette question est à poser pour les personnes âgées de 3 ans ou plus."
    }
        ]
        search_results = MilvusService().search(input.question)
        prompt = PromptFactory.get_navigation_prompt(input.question, search_results)
        response = await llm_manager.generate(prompt, provider_name=provider, temperature=temperature)
        return success_response(data=response, status_code=200)
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        # logger.warning(traceback_str)
        raise Exception(str(e))

@router.get("/initmilvus")
async def init_milvus():
    try:
        MilvusService()
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        raise Exception(str(e))
    
@router.get("/embedded")
async def embed(input: Optional[TextInput] = Body(default=None)):
    try:
        if input is None:
            raise BadRequestException("Donnée manquant")
        data = generate_embedding(input.text)
        return success_response(data=data, status_code=200)
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        # logger.warning(traceback_str)
        raise Exception(str(e))


@router.get("/consoles_to_create")
def read_surveys():
    try:
        rows: List[ConsoleItem] = fetch_consoles_to_create()
        survey = rows[0] if rows else None
        data = {"id":survey.id,"nom": survey.nom,"emplacement":survey.emplacement,"content":survey.content}
        return success_response(data=data, status_code=200)
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        raise Exception(str(e))

@router.post("/clean_collection")
def read_surveys():
    try:
        MilvusService()._clean_collection() 
        MilvusService()
        return success_response(message="collection cleaned successfully",status_code=201)
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.warning(traceback_str)
        raise Exception(str(e))
    
@router.post("/surveys_milvus")
def update_surveys_milvus():
    try:
        message = MilvusService().bulk_insert_surveys_to_milvus()
        return success_response(message=message,status_code=201)
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.warning(traceback_str)
        raise Exception(str(e))

@router.post("/consoles_milvus")
def update_consoles_milvus():
    try:
        message = MilvusService().bulk_insert_consoles_to_milvus()
        # raise BadRequestException()
        return success_response(message=message,status_code=201)
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.warning(traceback_str)
        raise Exception(str(e))
        

@router.get("/surveys_milvus")
def read_surveys_milvus():
    try:
        rows = MilvusService().list_surveys()   
        return success_response(data = rows,status_code=200)
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.warning(traceback_str)
        raise Exception(str(e))

@router.get("/consoles_milvus")
def read_consoles_milvus():
    try: 
        rows = MilvusService().list_consoles()   
        return success_response(data = rows,status_code=200)
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.warning(traceback_str)
        raise Exception(str(e))

@router.delete("/surveys_milvus")
def update_surveys_milvus():
    try:
        message = MilvusService().delete_surveys_milvus()
        return success_response(message=message,status_code=200)
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.warning(traceback_str)
        raise Exception(str(e))

@router.get("/surveys_to_delete")
def read_surveys():
    try:
        rows = fetch_surveys_to_delete()
        return success_response(data=rows, status_code=200)
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        raise Exception(str(e))

@router.get("/test")
def read_test():
    # always the status_code except predefined httpexception status_code
    # raise HTTPException(status_code=500, detail="detail")
    raise ValueControlException(detail="detail")
    # always 500
    raise Exception("exception")

