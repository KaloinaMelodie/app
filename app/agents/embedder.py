from langchain_ollama import OllamaEmbeddings
from typing import List
import requests
import httpx
from app.core import settings
import os
from google.api_core.exceptions import GoogleAPIError
import vertexai
from vertexai.language_models import TextEmbeddingModel


# mxbai-embed-large 3s bge-m3 20s
embedder = OllamaEmbeddings(model="mxbai-embed-large",base_url=f"https://{settings.ollama_host}:{settings.ollama_port}",keep_alive=-1)

try:
    from vertexai.language_models import TextEmbeddingInput
    _HAS_TEXT_EMBEDDING_INPUT = True
except Exception:
    TextEmbeddingInput = None
    _HAS_TEXT_EMBEDDING_INPUT = False

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
GCP_VERTEX_LOCATION = os.getenv("GCP_VERTEX_LOCATION", "us-central1")
GCP_EMBED_MODEL = os.getenv("GCP_EMBED_MODEL", "text-multilingual-embedding-002")
_vertex_initialized = False
_text_embed_model = None

def _ensure_vertex_init():
    global _vertex_initialized, _text_embed_model
    if not _vertex_initialized:
        if not GCP_PROJECT_ID:
            raise RuntimeError("GCP_PROJECT_ID manquant (env).")
        if not GCP_VERTEX_LOCATION:
            raise RuntimeError("GCP_VERTEX_LOCATION manquant (env).")
        vertexai.init(project=GCP_PROJECT_ID, location=GCP_VERTEX_LOCATION)
        _text_embed_model = TextEmbeddingModel.from_pretrained(GCP_EMBED_MODEL)
        _vertex_initialized = True

def generate_embedding_gemini(text: str) -> List[float]:
    try:
        _ensure_vertex_init()
        if _HAS_TEXT_EMBEDDING_INPUT:
            inputs = [TextEmbeddingInput(text=text, task_type="RETRIEVAL_QUERY")]
            resp = _text_embed_model.get_embeddings(inputs)
        else:
            resp = _text_embed_model.get_embeddings([text])
        return resp[0].values
    except GoogleAPIError as e:
        raise Exception(f"Vertex AI error: {e.__class__.__name__}: {e}")
    except Exception as e:
        raise Exception(f"Vertex AI error: {e}")

def embed_query_batch_gemini(texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> List[List[float]]:
    if not texts:
        return []
    try:
        _ensure_vertex_init()
        if _HAS_TEXT_EMBEDDING_INPUT:
            inputs = [TextEmbeddingInput(text=t, task_type=task_type) for t in texts]
            resp = _text_embed_model.get_embeddings(inputs)
        else:
            resp = _text_embed_model.get_embeddings(texts)
        return [emb.values for emb in resp]
    except GoogleAPIError as e:
        raise Exception(f"Vertex AI error: {e.__class__.__name__}: {e}")
    except Exception as e:
        raise Exception(f"Vertex AI error: {e}")

def generate_embedding(text: str) -> list:
    try:
        return embedder.embed_query(text) 
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        raise Exception("cannot connect to Ollama server")

def embed_query_batch(texts: List[str]) -> List[List[float]]:
    try:    
        return embedder.embed_documents(texts)
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
            raise Exception("cannot connect to Ollama server")
    

