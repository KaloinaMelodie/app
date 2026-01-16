from pydantic import BaseModel, HttpUrl
from typing import Optional

class Job(BaseModel):
    url: HttpUrl
    wait_ms: Optional[int] = 3500
    timeout_ms: Optional[int] = 20000
