from fastapi import APIRouter, Depends, Query, status
from src.security import require_admin
from src.schemas.author import MangaAuthor
from src.models import author as author_model
from src.schemas.general import Pagination
from src.db import get_db
from asyncpg import Connection


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/roles", status_code=status.HTTP_200_OK, response_model=Pagination[MangaAuthor])
async def get_manga_authors(
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
): 
    await author_model.get_manga_authors_pagination(limit, offset, conn)