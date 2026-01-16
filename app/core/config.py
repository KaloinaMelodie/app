import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
dotenv_path = os.path.join(BASE_DIR, ".env")
 
logger.warning("Loading .env from %s", dotenv_path)

if os.getenv("DISABLE_DOTENV") != "1":
    load_dotenv(dotenv_path=dotenv_path, override=False)

APP_ENV = os.getenv("APP_ENV", "dev").lower()

env_filename = (
    ".env.production" if APP_ENV in ["prod", "production"] else ".env"
)

dotenv_path = os.path.join(BASE_DIR, env_filename)
 
logger.warning("Environment detected: %s", APP_ENV)
logger.warning("Loading .env from %s", dotenv_path)

if os.getenv("DISABLE_DOTENV") != "1" and os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path, override=False)
else:
    logger.info("Skipping dotenv load (DISABLE_DOTENV=%s)", os.getenv("DISABLE_DOTENV"))


class Settings(BaseSettings):
    milvus_host: str
    milvus_apikey: str
    milvus_port: str
    ollama_host: str
    ollama_port: str
    hive_host: str
    hive_port: str
    openrouter_baseurl: str
    openrouter_apikey: str
    gcp_project_id: str
    google_application_credentials: str
    gcp_translate_location: str  
    gcp_vertex_location: str
    gcp_embed_model: str
    locales_dir: str
    jwt_secret: str
    env: str
    cors_allow_origins: str
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "chatdb"
    app_env: str = "dev"
    admins_bootstrap_emails: str

    model_config = SettingsConfigDict(env_file=dotenv_path)

settings = Settings()
