from fastapi import APIRouter, Depends, status
from src.schemas.genre import Genre
from src.schemas.general import Pagination
from src.models import genre as genre_model
from src.db import get_db
from asyncpg import Connection


router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK, response_model=Pagination[Genre])
async def get_genres(conn: Connection = Depends(get_db)):
    return await genre_model.get_genres(1000, 0, conn)