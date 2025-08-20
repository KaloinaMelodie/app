from langchain_ollama import OllamaEmbeddings
from typing import List
import requests
import httpx
from app.core import settings


embedder = OllamaEmbeddings(model="mxbai-embed-large",base_url=f"http://{settings.ollama_host}:{settings.ollama_port}",keep_alive=-1)

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

