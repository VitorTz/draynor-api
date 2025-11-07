from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Collection(BaseModel):

    id: int
    title: str
    descr: Optional[str]
    created_at: datetime


class CollectionCreate(BaseModel):

    title: str
    descr: Optional[str]


class CollectionUpdate(BaseModel):

    id: int
    title: Optional[str]
    descr: Optional[str]


class CollectionMangaCreate(BaseModel):

    collection_id: int
    manga_id: int


class CollectionMangaDelete(BaseModel):

    collection_id: int
    manga_id: int