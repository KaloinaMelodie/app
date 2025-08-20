from pydantic import BaseModel
from typing import List, Optional

class SurveyItem(BaseModel):
    id: Optional[str]
    rev: Optional[int]
    nom: Optional[str]
    langue: Optional[str]
    emplacement: Optional[List[str]]
    accessright: Optional[List[str]]
    content: Optional[str]
