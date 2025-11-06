from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from src.security import require_admin
from src.schemas.author import MangaAuthor, MangaAuthorList, MangaAuthorCreate, MangaAuthorDelete
from src.models import author as author_model
from src.schemas.general import Pagination, IntId
from src.db import get_db
from asyncpg import Connection


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/", status_code=status.HTTP_200_OK, response_model=MangaAuthorList)
async def get_manga_authors(manga: IntId, conn: Connection = Depends(get_db)):
    return await author_model.get_manga_authors(manga, conn)


@router.get("/all", status_code=status.HTTP_200_OK, response_model=Pagination[MangaAuthor])
async def get_all_manga_authors(
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
): 
    return await author_model.get_manga_authors_pagination(limit, offset, conn)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_manga_author(
    manga_author: MangaAuthorCreate,
    conn: Connection = Depends(get_db)
):
    await author_model.create_manga_author(manga_author, conn)
    return Response()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_manga_author(manga_author: MangaAuthorDelete, conn: Connection = Depends(get_db)):
    await author_model.delete_manga_author(manga_author, conn)