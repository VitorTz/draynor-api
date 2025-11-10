from src.schemas.reading_status import (
    MangaReadingStatus, 
    ReadingStatusLiteral, 
    ReadingStatusCreate,
    DeleteReadingStatus
)
from fastapi import APIRouter, Depends, status, Query
from fastapi.responses import Response
from src.schemas.general import IntId, Pagination
from src.schemas.user import User
from src.schemas.manga import Manga
from src.models import library as library_model
from src.security import get_user_from_token
from asyncpg import Connection
from src.db import get_db


router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK, response_model=Pagination[Manga])
async def get_mangas_by_reading_status(
    reading_status: ReadingStatusLiteral = Query(default='Reading'),
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_user_from_token),
    conn: Connection = Depends(get_db)
):
    return await library_model.get_mangas_by_reading_status(
        reading_status, 
        user, 
        limit, 
        offset, 
        conn
    )


@router.get("/manga", status_code=status.HTTP_200_OK, response_model=MangaReadingStatus)
async def get_manga_reading_status(
    manga_id: int = Query(...),
    user: User = Depends(get_user_from_token),
    conn: Connection = Depends(get_db)
):
    return await library_model.get_manga_reading_status(manga_id, user, conn)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_manga_reading_status(
    reading_status: ReadingStatusCreate,
    user: User = Depends(get_user_from_token),
    conn: Connection = Depends(get_db)
):
    await library_model.upsert_reading_status(
        reading_status,
        user,
        conn
    )
    return Response()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_manga_reading_status(
    reading_status: DeleteReadingStatus,
    user: User = Depends(get_user_from_token),
    conn: Connection = Depends(get_db)
):
    await library_model.delete_reading_status(reading_status, user, conn)