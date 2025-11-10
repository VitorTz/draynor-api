from fastapi import APIRouter, Depends, Query, status
from src.security import require_admin
from src.schemas.genre import Genre, GenreCreate, GenreDelete
from src.models import genre as genre_model
from src.schemas.general import Pagination, IntId
from src.db import get_db
from asyncpg import Connection
from typing import Optional


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/", status_code=status.HTTP_200_OK, response_model=Pagination[Genre])
async def get_genres(
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    genre_name: Optional[str] = Query(default=None, description='Buscar por gênero exato'),
    conn: Connection = Depends(get_db)
):
    return await genre_model.get_genres(limit, offset, conn, genre_name)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Genre)
async def create_genre(
    genre: GenreCreate,
    conn: Connection = Depends(get_db)
):
    return await genre_model.create_genre(genre, conn)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_genre(genre: IntId, conn: Connection = Depends(get_db)):
    await genre_model.delete_genre(genre, conn)
