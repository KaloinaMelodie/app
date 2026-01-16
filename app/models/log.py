from typing import Optional, List, Type, TypeVar, Any, Dict, Union
from pydantic import BaseModel, ConfigDict, field_validator
import json

class LogItem(BaseModel):
    ts: Optional[str] = None
    stage: Optional[str] = None
    event: Optional[str] = None
    msg: Optional[str] = None
    attempt: Optional[int] = None
    waitMs: Optional[int] = None
    tag: Optional[str] = None
    source: Optional[str] = None