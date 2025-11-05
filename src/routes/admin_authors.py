from fastapi import APIRouter, Depends, Query, status
from src.security import require_admin
from src.schemas.author import Author, AuthorCreate, MangaAuthor
from src.models import author as author_model
from src.schemas.general import Pagination, IntId
from src.db import get_db
from asyncpg import Connection


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/", status_code=status.HTTP_200_OK, response_model=Pagination[Author])
async def get_authors(
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await author_model.get_authors(limit, offset, conn)



@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Author)
async def create_author(
    author: AuthorCreate,
    conn: Connection = Depends(get_db)
):
    return await author_model.create_author(author, conn)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_author(
    author: IntId,
    conn: Connection = Depends(get_db)
):
    await author_model.delete_author(author, conn)
