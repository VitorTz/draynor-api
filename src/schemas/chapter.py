from pydantic import BaseModel
from datetime import datetime


class Chapter(BaseModel):

    id: int
    manga_id: int
    chapter_index: int
    chapter_name: str
    created_at: datetime


class ChapterImage(BaseModel):

    chapter_id: int
    image_index: int
    image_url: int
    width: int
    height: int