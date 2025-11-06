from fastapi import APIRouter, Depends, status, Query
from src.schemas.general import IntId
from src.schemas.chapter import MangaChapters, ChapterImageList
from src.models import chapter as chapter_model
from src.models import chapter_images as chapter_images_model
from src.db import get_db
from asyncpg import Connection
from typing import Optional, Literal


router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK, response_model=MangaChapters)
async def get_manga_chapters_by_manga_id(
    manga: IntId,
    limit: Optional[int] = Query(default=None, ge=0),
    order: Literal['ASC', 'DESC'] = Query(default='ASC', description='ASC or DESC'),
    conn: Connection = Depends(get_db)
):
    return await chapter_model.get_manga_chapters(manga, limit, order, conn)


@router.get("/images", status_code=status.HTTP_200_OK, response_model=ChapterImageList)
async def get_chapter_images(
    chapter: IntId,
    conn: Connection = Depends(get_db)
):
    return await chapter_images_model.get_chapter_images(chapter, conn)