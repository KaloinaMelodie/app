from typing import List, Literal
from app.models.question import User
from pydantic import BaseModel, Field
from typing import List, Optional
from pydantic import BaseModel, AnyHttpUrl

from app.models.page import GifItem, ImageItem, VideoItem

Role = Literal["system", "user", "assistant"]

class Message(BaseModel):
    role: Role
    content: str = Field(..., min_length=1)

class ChatRequest(BaseModel):
    user: User
    messages: List[Message]
    question: str = Field(..., min_length=1)
    temperature: float = 0.7
    max_input_tokens: int = 2048
    max_output_tokens: int = 2048
    max_messages: int | None = 50
    partitions: Optional[List[str]] = None

class ChatResponse(BaseModel):
    reply: str


class SourceMeta(BaseModel):
    doc_id: str
    url: Optional[str] = None
    breadcrumbs: Optional[List[str]] = None
    images: Optional[List[ImageItem]] = None
    gifs: Optional[List[GifItem]] = None
    videos: Optional[List[VideoItem]] = None

class TrainingResponse(BaseModel):
    reply: str
    sources: List[SourceMeta] = []