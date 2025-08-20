from pydantic import BaseModel, model_validator
from typing import Optional
from app.exceptions import *

class TextInput(BaseModel):
    text: Optional[str] = None

    @model_validator(mode="after")
    def validate_text(cls, model):
        if not model.text or not model.text.strip():
            raise ValueControlException("Le champ 'text' est vide ou manquant")
        return model