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

router = APIRouter(prefix="/multilingual", tags=["multilingual"])

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
        survey = rows[0] if rows else None
        data = {"id":survey.id,"nom": survey.nom,"emplacement":survey.emplacement,"content":survey.content}
        return success_response(data=data, status_code=200)
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