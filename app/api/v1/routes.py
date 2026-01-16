from fastapi import APIRouter, HTTPException, Body,Query
from app.models import SurveyItem,ConsoleItem
from app.models import TextInput,QuestionInput, LogItem
from app.services.milvus_multilingual_service import MilvusMultilingualService
from app.services.hive_service import fetch_consoles_to_create, fetch_logs, fetch_some_surveys,fetch_surveys_to_create,fetch_surveys_to_delete
from app.agents.embedder import generate_embedding, generate_embedding_gemini
from app.exceptions.exceptions import *
from app.core.responses import *
from app.agents import *
from typing import List, Optional
from app.prompt import PromptFactory
import logging
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import os
from fastapi.encoders import jsonable_encoder



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
router = APIRouter()

llm_manager = LLMManager([
    # OllamaProvider(model="llama3.2"),
    GeminiProvider(
        model="gemini-2.5-pro",        # "gemini-2.5-flash"        
        location="europe-west1"
    ),
    # OpenRouterProvider(model="mistralai/mixtral-8x7b", api_key="sk-...")
])

@router.get("/generate")
async def generate(
    input: Optional[QuestionInput] = Body(default = None),
    provider: str = Query("vertex-gemini"),
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

        search_results = MilvusMultilingualService().search(input.question,input.user)
        response = search_results
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
        MilvusMultilingualService()
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
    
@router.get("/embedded_gemini")
async def embed_gemini(input: Optional[TextInput] = Body(default=None)):
    try:
        if input is None:
            raise BadRequestException("Donnée manquant") 
        data = generate_embedding_gemini(input.text)
        return success_response(data=data, status_code=200)
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        # logger.warning(traceback_str)
        raise Exception(str(e))


@router.get("/consoles_to_create")
def read_consoles():
    try:
        rows: List[ConsoleItem] = fetch_consoles_to_create()
        # survey = rows[0] if rows else None
        # data = {"id":survey.id,"nom": survey.nom,"emplacement":survey.emplacement,"content":survey.content}
        return success_response(data=jsonable_encoder(rows), status_code=200)
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        raise Exception(str(e))

@router.get("/surveys_to_create")
def read_surveys():
    try:
        rows: List[ConsoleItem] = fetch_surveys_to_create()
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
        MilvusMultilingualService()._clean_collection() 
        MilvusMultilingualService()
        return success_response(message="collection cleaned successfully",status_code=201)
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.warning(traceback_str)
        raise Exception(str(e))

@router.post("/clean_formation_collection")
def read_surveys():
    try:
        MilvusMultilingualService()._clean_formation_collection() 
        MilvusMultilingualService()
        return success_response(message="formation collection cleaned successfully",status_code=201)
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
        message = MilvusMultilingualService().bulk_insert_surveys_to_milvus()
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
        message = MilvusMultilingualService().bulk_insert_consoles_to_milvus()
        return success_response(message=message,status_code=201)
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.warning(traceback_str)
        raise Exception(str(e))
    
@router.post("/documents_milvus")
def update_documents_milvus():
    try:
        message = MilvusMultilingualService().bulk_insert_documents_to_milvus()
        return success_response(message=message,status_code=201)
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.warning(traceback_str)
        raise Exception(str(e))

@router.post("/pages_milvus")
def update_pages_milvus():
    try:
        message = MilvusMultilingualService().bulk_insert_pages_to_milvus()
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
        rows = MilvusMultilingualService().list_surveys()   
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
        rows = MilvusMultilingualService().list_consoles()   
        return success_response(data = rows,status_code=200)
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.warning(traceback_str)
        raise Exception(str(e))

@router.get("/documents_milvus") 
def read_documents_milvus():
    try: 
        rows = MilvusMultilingualService().list_documents()   
        return success_response(data = rows,status_code=200)
    except HTTPException as he:
        raise he  
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.warning(traceback_str)
        raise Exception(str(e))

@router.get("/pages_milvus") 
def read_pages_milvus():
    try: 
        rows = MilvusMultilingualService().list_pages()   
        return success_response(data = rows,status_code=200)
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.warning(traceback_str)
        raise Exception(str(e))

@router.delete("/surveys_milvus")
def delete_surveys_milvus():
    try:
        message = MilvusMultilingualService().delete_surveys_milvus()
        return success_response(message=message,status_code=200)
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.warning(traceback_str)
        raise Exception(str(e))

@router.delete("/consoles_milvus")
def delete_consoles_milvus():
    try:
        message = MilvusMultilingualService().delete_consoles_milvus()
        return success_response(message=message,status_code=200)
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.warning(traceback_str)
        raise Exception(str(e))

@router.delete("/documents_milvus")
def delete_documents_milvus():
    try:
        message = MilvusMultilingualService().delete_documents_milvus()
        return success_response(message=message,status_code=200)
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.warning(traceback_str)
        raise Exception(str(e))

@router.delete("/consoles_partition")
def delete_consoles_partition():
    try:
        message = MilvusMultilingualService()._clean_console_partition()
        return success_response(message=message,status_code=200)
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.warning(traceback_str)
        raise Exception(str(e))
    
@router.delete("/documents_partition")
def delete_documents_partition():
    try:
        message = MilvusMultilingualService()._clean_document_partition()
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

@router.get("/logs")
def read_logs():
    try:
        rows = fetch_logs()
        return success_response(data=jsonable_encoder(rows), status_code=200)
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        raise Exception(str(e))