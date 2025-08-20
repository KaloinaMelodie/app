from pydantic import BaseModel, model_validator
from typing import Optional
from app.exceptions import *

class QuestionInput(BaseModel):
    question: Optional[str] = None

    @model_validator(mode="after")
    def validate_question(cls, model):
        if not model.question or not model.question.strip():
            raise ValueControlException("Le champ 'question' est vide ou manquant")
        return model