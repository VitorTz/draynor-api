from fastapi import APIRouter, Depends, Query, status
from src.security import require_admin
from src.schemas.manga import Manga, MangaCreate, MangaUpdate
from src.models import manga as manga_model
from src.schemas.general import Pagination, IntId
from src.db import get_db
from typing import Optional
from asyncpg import Connection


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/", status_code=status.HTTP_200_OK, response_model=Pagination[Manga])
async def get_mangas(
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    q: Optional[str] = Query(default=None, description="Permite buscar por um manga pelo título"),
    title: Optional[str] = Query(default=None, description='Busca pelo titulo exato'),
    conn: Connection = Depends(get_db)
):
    return await manga_model.get_mangas(limit, offset, conn, q, title)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Manga)
async def create_manga(manga: MangaCreate, conn: Connection = Depends(get_db)):
    return await manga_model.create_manga(manga, conn)


@router.put("/", status_code=status.HTTP_201_CREATED, response_model=Optional[Manga])
async def update_manga(manga: MangaUpdate, conn: Connection = Depends(get_db)):
    return await manga_model.update_manga(manga, conn)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_manga(manga: IntId, conn: Connection = Depends(get_db)):
    await manga_model.delete_manga(manga, conn)