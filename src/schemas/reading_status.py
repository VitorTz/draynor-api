from pydantic import BaseModel
from typing import Literal
from uuid import UUID
from datetime import datetime


ReadingStatusLiteral = Literal['Reading', 'Completed', 'On Hold', 'Dropped', 'Plan to Read', 'Rereading']


class ReadingStatusCreate(BaseModel):

    manga_id: int
    reading_status: ReadingStatusLiteral


class MangaReadingStatus(BaseModel):

    id: int
    manga_id: int
    user_id: UUID
    reading_status: ReadingStatusLiteral
    created_at: datetime
    updated_at: datetime


class DeleteReadingStatus(BaseModel):

    manga_id: int