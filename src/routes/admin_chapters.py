from fastapi import APIRouter, Depends, Query, status
from src.security import require_admin
from src.schemas.chapter import Chapter, ChapterCreate, ChapterUpdate
from src.models import chapter as chapter_model
from src.schemas.general import Pagination, IntId
from typing import Optional
from src.db import get_db
from asyncpg import Connection


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/", status_code=status.HTTP_200_OK, response_model=Pagination[Chapter])
async def get_chapters(
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    manga_id: Optional[int] = Query(default=None),
    conn: Connection = Depends(get_db)
):
    return await chapter_model.get_chapters(limit, offset, conn, manga_id)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Chapter)
async def create_chapter(chapter: ChapterCreate, conn: Connection = Depends(get_db)) -> Chapter:
    return await chapter_model.create_chapter(chapter, conn)


@router.put("/", status_code=status.HTTP_201_CREATED, response_model=Chapter)
async def update_chapter(chapter: ChapterUpdate, conn: Connection = Depends(get_db)) -> Chapter:
    return chapter_model.update_chapter(chapter, conn)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chapter(chapter: IntId, conn: Connection = Depends(get_db)) -> None:
    await chapter_model.delete_chapter(chapter, conn)


@router.delete("/all", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_chapters(conn: Connection = Depends(get_db)):
    await chapter_model.delete_all_chapters(conn)