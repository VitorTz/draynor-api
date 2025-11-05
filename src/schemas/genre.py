from pydantic import BaseModel
from datetime import datetime
from typing import List


class Genre(BaseModel):

    id: int
    genre: str
    created_at: datetime


class MangaGenre(BaseModel):

    genre_id: int
    manga_id: int


class GenreCreate(BaseModel):

    genre: str


class GenreDelete(BaseModel):

    id: int


class MangaGenreCreate(BaseModel):

    manga_id: int
    genre_id: int


class MangaGenreDelete(BaseModel):

    manga_id: int
    genre_id: int


class MangaGenreList(BaseModel):
    
    manga_id: int
    genres: List[Genre]