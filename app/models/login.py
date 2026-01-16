from pydantic import BaseModel
from typing import List, Optional

class LoginIn(BaseModel):
    username: str
    password: str

class TokenData(BaseModel):
    sub: str              
    email: Optional[str]  
    name: Optional[str]
    is_admin: bool
    exp: int