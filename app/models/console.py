from pydantic import BaseModel
from typing import List, Optional

class ConsoleItem(BaseModel):
    id: Optional[str]
    rev: Optional[int]
    nom: Optional[str]
    emplacement: Optional[List[str]]
    content: Optional[str]
