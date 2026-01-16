from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional
from datetime import datetime
from app.exceptions import *

class AdminCreate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None


class AdminUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None

class AdminOut(BaseModel):
    id: str
    email: Optional[str] = None
    username: Optional[str] = None
    created_at_server: datetime
    updated_at_server: datetime
