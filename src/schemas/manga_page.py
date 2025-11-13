from pydantic import BaseModel
from src.schemas.manga import Manga
from src.schemas.chapter import Chapter
from src.schemas.reading_status import ReadingStatusLiteral
from src.schemas.genre import Genre
from src.schemas.author import MangaAuthor
from typing import List, Optional


class MangaPageChapter(BaseModel):

    id: int
    chapter_name: str


class MangaPageData(BaseModel):

    manga: Manga
    manga_num_views: int
    genres: List[Genre]
    authors: List[MangaAuthor]
    reading_status: Optional[ReadingStatusLiteral]
    chapters: List[MangaPageChapter]


class MangaCarouselItem(BaseModel):

    manga: Manga    
    genres: List[Genre]
    authors: List[MangaAuthor]
