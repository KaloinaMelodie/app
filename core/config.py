import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
dotenv_path = os.path.join(BASE_DIR, ".env")
 
logger.warning("Loading .env from %s", dotenv_path)

load_dotenv(dotenv_path=dotenv_path)

class Settings(BaseSettings):
    milvus_host: str
    milvus_port: str
    ollama_host: str
    ollama_port: int
    hive_host: str
    hive_port: str
    openrouter_baseurl: str
    openrouter_apikey: str
    gcp_project_id: str
    google_application_credentials: str
    gcp_translate_location: str
    locales_dir: str

    model_config = SettingsConfigDict(env_file=dotenv_path)

settings = Settings()
