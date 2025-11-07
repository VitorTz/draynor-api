from pydantic import BaseModel
from datetime import datetime
from typing import Optional



class MangaRequest(BaseModel):

    id: int
    title: str
    message: Optional[str]
    created_at: datetime


class MangaRequestCreate(BaseModel):

    title: str
    message: Optional[str] = None
    