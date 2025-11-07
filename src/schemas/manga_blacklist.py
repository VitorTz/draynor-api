from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BlackListManga(BaseModel):

    manga_id: int
    descr: Optional[str]
    created_at: datetime


class BlackListMangaCreate(BaseModel):

    manga_id: int
    descr: Optional[str] = None

