from fastapi import FastAPI,APIRouter
from app.api.v1.routes import router as api_router_v1
from app.exceptions import validation_exception_handlers,exception_handlers,http_exception_handler
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="APP", version="1.0.0")

app.mount("/v1", api_router_v1) # /v1/docs 
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

api_v1 = APIRouter(prefix="/v1")
api_v1.include_router(api_router_v1)

validation_exception_handlers(app)
exception_handlers(app)
http_exception_handler(app)
app.include_router(api_v1)


