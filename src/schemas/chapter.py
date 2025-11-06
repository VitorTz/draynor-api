from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from src.schemas.manga import Manga


class Chapter(BaseModel):

    id: int
    manga_id: int
    chapter_index: int
    chapter_name: str
    created_at: datetime


class ChapterCreate(BaseModel):

    chapter_id: int
    manga_id: int
    chapter_index: int
    chapter_name: str


class ChapterUpdate(BaseModel):

    id: int
    chapter_index: Optional[int] = None
    chapter_name: Optional[str] = None


class MangaChapters(BaseModel):

    manga_id: int
    chapters: List[Chapter]


class ChapterImage(BaseModel):

    chapter_id: int
    image_index: int
    image_url: str
    width: int
    height: int
    created_at: datetime


class ChapterImageDelete(BaseModel):

    chapter_id: int
    image_index: int


class ChapterImageCreate(BaseModel):

    chapter_id: int
    image_index: int
    image_url: str
    width: int
    height: int


class ChapterImageListCreate(BaseModel):

    chapter_id: int
    images: List[ChapterImageCreate]


class ChapterImageList(BaseModel):

    manga: Optional[Manga]
    chapter: Optional[Chapter]
    num_images: int
    images: List[ChapterImage]