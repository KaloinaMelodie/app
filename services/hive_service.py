from pyhive import hive
from TCLIService.ttypes import TApplicationException
from contextlib import contextmanager
import json
from typing import List, Type, TypeVar
from pydantic import BaseModel
from app.models import SurveyItem,ConsoleItem
import logging
from app.core import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HIVE_HOST = settings.hive_host
HIVE_PORT = settings.hive_port
HIVE_USER = "vagrant"
T = TypeVar("T", bound=BaseModel)

def hive_rows_to_models(cursor, model_class: Type[T]) -> List[T]:
    def clean_column(col: str) -> str:
        return col.split('.')[-1]  

    columns = [clean_column(desc[0]) for desc in cursor.description]
    results = []
    
    for row in cursor.fetchall():
        data = dict(zip(columns, row))
       
        for field in ["emplacement", "accessright"]:
            if field in data and isinstance(data[field], str):
                try:
                    data[field] = json.loads(data[field])
                except json.JSONDecodeError:
                    pass  

        results.append(model_class(**data))

    return results

@contextmanager
def hive_cursor():
    try:
        conn = hive.Connection(host=HIVE_HOST, port=HIVE_PORT, username=HIVE_USER)
        cursor = conn.cursor()
        yield cursor
    except TApplicationException as e:
        print(f"Hive error: {e}")
        raise
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def fetch_some_surveys(limit=10):
    with hive_cursor() as cursor:
        cursor.execute(f"SELECT *  FROM surveys_with_content LIMIT {limit}")
        return hive_rows_to_models(cursor, SurveyItem)

def fetch_surveys_to_create():
    logger.info("fetch surveys to create ...")
    with hive_cursor() as cursor:
        cursor.execute(f"SELECT * FROM surveys_to_insert_or_update")
        return hive_rows_to_models(cursor, SurveyItem)

def fetch_consoles_to_create():
    logger.info("fetch consoles to create ...")
    with hive_cursor() as cursor:
        cursor.execute(f"SELECT * FROM consoles_to_insert_or_update")
        return hive_rows_to_models(cursor, ConsoleItem)

def fetch_surveys_to_delete():
    with hive_cursor() as cursor:
        cursor.execute(f"SELECT to_delete FROM surveys_id_sync")
        rows = cursor.fetchall()
        return [row[0] for row in rows if row[0] is not None]
    
def fetch_consoles_to_delete():
    with hive_cursor() as cursor:
        cursor.execute(f"SELECT to_delete FROM consoles_id_sync")
        rows = cursor.fetchall()
        return [row[0] for row in rows if row[0] is not None]