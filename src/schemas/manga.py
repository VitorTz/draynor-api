from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Manga(BaseModel):

    id: int
    title: str
    descr: Optional[str] = None
    cover_image_url: str
    status: str
    color: str
    updated_at: datetime
    created_at: datetime
    mal_url: Optional[str] = None


class MangaCreate(BaseModel):

    title: str
    descr: Optional[str] = None
    cover_image_url: str
    status: str
    color: str
    mal_url: Optional[str] = None


class MangaUpdate(BaseModel):

    id: int
    title: Optional[str] = None
    descr: Optional[str] = None
    cover_image_url: Optional[str] = None
    status: Optional[str] = None
    color: Optional[str] = None    
    mal_url: Optional[str] = None