from pydantic import BaseModel
from typing import List, Optional

class MemoryCreate(BaseModel):
    text: str
    type: Optional[str] = "note"
    importance: Optional[int] = 1
    tags: Optional[List[str]] = []

class RecallQuery(BaseModel):
    query: str
    tags: Optional[List[str]] = []
    k: Optional[int] = 5
