from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from src.security import require_admin
from src.schemas.genre import MangaGenreList, MangaGenreCreate, MangaGenre
from src.models import genre as genre_model
from src.schemas.general import Pagination, IntId
from src.db import get_db
from asyncpg import Connection
from typing import Optional


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/", status_code=status.HTTP_200_OK, response_model=MangaGenreList)
async def get_manga_genres(manga: IntId, conn: Connection = Depends(get_db)):
    return await genre_model.get_manga_genres(manga, conn)


@router.get("/all", status_code=status.HTTP_200_OK, response_model=Pagination[MangaGenre])
async def get_all_manga_genres(
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await genre_model.get_manga_genres_pagination(limit, offset, conn)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_manga_genre(manga_genre: MangaGenreCreate, conn: Connection = Depends(get_db)):
    await genre_model.create_manga_genre(manga_genre, conn)
    return Response()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_manga_genre(manga_genre: MangaGenre, conn: Connection = Depends(get_db)):
    await genre_model.delete_manga_genre(manga_genre, conn)