import os
import asyncio
import pytest
from httpx import AsyncClient
from asgi_lifespan import LifespanManager

os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGO_DB", "chatdb_test")
os.environ.setdefault("APP_ENV", "test")

from app.main import app
from app.db import get_db

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session")
async def test_app():    
    async with LifespanManager(app):
        yield app

@pytest.fixture
async def client(test_app):
    async with AsyncClient(app=test_app, base_url="http://testserver") as ac:
        yield ac

@pytest.fixture(autouse=True)
async def clean_db():    
    db = get_db()
    for name in ("conversations", "messages"):
        await db[name].delete_many({})
    yield    
    for name in ("conversations", "messages"):
        await db[name].delete_many({})
