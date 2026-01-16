from pydantic import BaseModel, model_validator
from typing import Optional
from app.exceptions import *

class User(BaseModel):
    client: Optional[str]= None
    email: Optional[str]= None
    user: Optional[str]= None
    username: Optional[str]= None
    createdAt: Optional[str]= None
    givenName: Optional[str]= None
    familyName: Optional[str]= None
    groups: Optional[list[str]]= None
    emailConfirmed: Optional[bool]= None
    ageConfirmed: Optional[bool]= None


class QuestionInput(BaseModel):
    question: Optional[str] = None
    user: Optional[User] = None

    @model_validator(mode="after")
    def validate_question(cls, model):
        if not model.question or not model.question.strip():
            raise ValueControlException("Le champ 'question' est vide ou manquant")
        return model