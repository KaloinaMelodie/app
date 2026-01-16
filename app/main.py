from fastapi import FastAPI,APIRouter
from app.api.v1 import router as api_router_v1
from app.api.v1 import chat_router as chat_router_v1
from app.api.v1 import translate_router as api_translate_router_v1
from app.api.v1 import auth_router as auth_router_v1
from app.api.v1 import bd_router as bd_router_v1
from app.api.v1 import admins_router as admins_router_v1
from app.api.v1 import render_router as render_router_v1
from app.api.v1.eval_export import router as eval_export_router_v1
from app.api.v1.eval_export_run import router as eval_export_run_router_v1
from app.api.v1.multilingual_routes import router as multilingual_router_v1
from app.exceptions import validation_exception_handlers,exception_handlers,http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from app.base.db import get_client, get_db
from app.base.indexes import ensure_indexes
import os
import sys, asyncio
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI(title="APP", version="1.0.0")

# app.mount("/v1", api_router_v1) # /v1/docs 
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
  
# CORS si utilises fetch() avec credentials: 'include'
origins = [o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",") if o.strip()] 

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,    
    allow_methods=["GET","POST","PUT","DELETE","OPTIONS","PATCH"],                  
    allow_headers=["Content-Type","Authorization","X-CSRF-Token"],
)

# if os.getenv("ENV") == "prod":
#     app.add_middleware(HTTPSRedirectMiddleware)

@app.middleware("http")
async def security_headers(request, call_next):
    resp = await call_next(request)
    if os.getenv("ENV") == "prod":
        # 1 jour (86 400 s), 1 ans 31536000
        resp.headers["Strict-Transport-Security"] = "max-age=86400; includeSubDomains"
    return resp

api_v1 = APIRouter(prefix="/v1")
api_v1.include_router(api_translate_router_v1)
api_v1.include_router(api_router_v1)
api_v1.include_router(auth_router_v1)
api_v1.include_router(chat_router_v1)
api_v1.include_router(admins_router_v1)
api_v1.include_router(render_router_v1)
api_v1.include_router(bd_router_v1)
api_v1.include_router(eval_export_router_v1)
api_v1.include_router(eval_export_run_router_v1)
api_v1.include_router(multilingual_router_v1)

validation_exception_handlers(app)
exception_handlers(app)
http_exception_handler(app)
app.include_router(api_v1)


@app.on_event("startup")
async def on_startup():
    _ = get_client()
    db = get_db()
    await ensure_indexes(db)

@app.on_event("shutdown")
async def on_shutdown():
    client = get_client()
    client.close()