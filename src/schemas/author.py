from pydantic import BaseModel
from datetime import datetime
from typing import Literal, List


class Author(BaseModel):

    id: int
    name: str
    created_at: datetime


class AuthorWithRole(BaseModel):

    id: int
    name: str
    role: Literal['Author', 'Artist']
    created_at: datetime


class MangaAuthor(BaseModel):

    author_name: str
    author_id: int
    role: Literal['Author', 'Artist']


class AuthorCreate(BaseModel):

    name: str


class AuthorUpdate(BaseModel):

    id: int
    name: str


class MangaAuthorCreate(BaseModel):

    author_id: int
    manga_id: int
    role: Literal['Author', 'Artist']


class MangaAuthorDelete(BaseModel):

    author_id: int
    manga_id: int
    role: Literal['Author', 'Artist']



class MangaAuthorList(BaseModel):

    manga_id: int
    authors: List[MangaAuthor]