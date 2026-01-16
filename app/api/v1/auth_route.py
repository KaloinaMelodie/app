from fastapi import FastAPI, HTTPException, Depends, Response, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, Optional, List
from app.models.login import LoginIn, TokenData
from app.services.admin_service import is_admin_in_db, is_bootstrap_admin
import os, json, httpx, time, datetime as dt
import jwt  
from jwt import PyJWTError
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
import logging  
from collections import defaultdict
import time
from app.base.db import get_db
from motor.motor_asyncio import AsyncIOMotorDatabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MWATER_LOGIN_URL = "https://api.mwater.co/v3/clients"

WINDOW, MAX_TRIES = 600, 5 # 10 min, 5 essais
FAILS = defaultdict(list)

# TODO what's the real value of this
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALG = "HS256" 
JWT_TTL_SECONDS = int(os.getenv("JWT_TTL_SECONDS", "7200"))  # 2h # TODO modify to 7200
# TODO what will happen in prod, the secure cookies
ENV = os.getenv("ENV", "dev")


async def is_admin(db: AsyncIOMotorDatabase, email: Optional[str], username: Optional[str]) -> bool:
    return await is_admin_in_db(db, email, username)

def create_jwt(sub: str, email: Optional[str], name: Optional[str], is_admin_flag: bool) -> str:
    exp = int(time.time()) + JWT_TTL_SECONDS
    payload = {
        "sub": sub,
        "email": email,
        "name": name,
        "is_admin": is_admin_flag,
        "exp": exp,
        "iat": int(time.time()),
        "iss": "your-fastapi"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def decode_jwt(token: str) -> TokenData:
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return TokenData(**data)
    except PyJWTError:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

COOKIE_NAME = "session"

def set_session_cookie(resp: Response, token: str):
    resp.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="strict",
        secure=(os.getenv("ENV","dev") == "prod"),
        max_age=JWT_TTL_SECONDS,            
        path="/",
    )

def clear_session_cookie(resp: Response):
    resp.delete_cookie(COOKIE_NAME, path="/")

def get_token_from_request(request: Request) -> str:
    cookie_token = request.cookies.get(COOKIE_NAME)
    if cookie_token:
        return cookie_token

    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1]

    raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="No token provided")

def current_user(token: str = Depends(get_token_from_request)) -> TokenData:
    return decode_jwt(token)

def require_admin(user: TokenData = Depends(current_user)) -> TokenData:
    if not user.is_admin:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Admin only")
    return user

def too_many_attempts(ip, username):
    now = time.time()
    key = (ip, (username or "").lower())
    FAILS[key] = [t for t in FAILS[key] if now - t < WINDOW]
    return len(FAILS[key]) >= MAX_TRIES

auth_router = APIRouter()

@auth_router.post("/auth/login")
async def login(payload: LoginIn, request: Request, response: Response, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        ip = request.client.host
        if too_many_attempts(ip, payload.username):
            raise HTTPException(status_code=429, detail="Trop de tentatives. Réessayez plus tard.")
        
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                r = await client.post(MWATER_LOGIN_URL, json={"username": payload.username, "password": payload.password})
            except httpx.RequestError as e:
                raise HTTPException(502, f"mWater unreachable: {e}")

        if r.status_code == 403:
            FAILS[(ip, (payload.username or "").lower())].append(time.time())
            raise HTTPException(403, r.json().get("error", "Invalid credentials"))
        if r.status_code != 200:
            raise HTTPException(502, f"mWater error {r.status_code}")

        FAILS[(ip, (payload.username or "").lower())] = []

        mwater_data: Dict[str, Any] = r.json()

        user_id = mwater_data.get("user")
        email = mwater_data.get("email")
        name = mwater_data.get("username") or mwater_data.get("givenName")
        username = (mwater_data.get("username")).strip().lower()

        admin_flag = await is_admin(db, email, username)
        if not admin_flag and is_bootstrap_admin(email): admin_flag = True


        token = create_jwt(sub=user_id or "", email=email, name=name, is_admin_flag=admin_flag)

        set_session_cookie(response, token)
        response.headers["Cache-Control"] = "no-store"

        enriched = dict(mwater_data)
        enriched["is_admin"] = admin_flag

        if os.getenv("ENV", "dev") == "dev":
            enriched["token_type"] = "bearer"
            enriched["access_token"] = token  

        return enriched
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        raise Exception(str(e))

@auth_router.post("/auth/logout")
def logout(response: Response):
    clear_session_cookie(response)
    return {"ok": True}

@auth_router.get("/auth/me")
def me(user: TokenData = Depends(current_user)):
    return {
        "sub": user.sub,
        "email": user.email,
        "name": user.name,
        "is_admin": user.is_admin,
        "exp": user.exp
    }


@auth_router.get("/admin/ping")
def admin_ping(_: TokenData = Depends(require_admin)):
    return {"pong": True, "at": dt.datetime.utcnow().isoformat() + "Z"}
