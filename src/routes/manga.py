from src.schemas.manga import Manga
from src.schemas.general import Pagination, IntId
from fastapi import APIRouter, Query, Depends, status
from src.models import manga as manga_model
from src.db import get_db
from asyncpg import Connection


router = APIRouter()


@router.get("/popular", status_code=status.HTTP_200_OK, response_model=Pagination[Manga])
async def get_most_popular_mangas(
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
) -> Pagination[Manga]:
    return await manga_model.get_popular_mangas(limit, offset, conn)


@router.get("/latest", status_code=status.HTTP_200_OK, response_model=Pagination[Manga])
async def get_latest_mangas(
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
) -> Pagination[Manga]:
    return await manga_model.get_latest_mangas(limit, offset, conn)


@router.get("/random", status_code=status.HTTP_200_OK, response_model=Pagination[Manga])
async def get_random_mangas(
    limit: int = Query(default=64, ge=0, le=64),
    conn: Connection = Depends(get_db)
) -> Pagination[Manga]:
    return await manga_model.get_random_mangas(limit, conn)


@router.get("/genre", status_code=status.HTTP_200_OK, response_model=Pagination[Manga])
async def get_manga_by_genre(
    genre: IntId,
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
) -> Pagination[Manga]:
    return await manga_model.get_manga_by_genre(genre, limit, offset, conn)