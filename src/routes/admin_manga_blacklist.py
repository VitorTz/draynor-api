from fastapi import APIRouter, Depends, Query, status
from src.security import require_admin
from src.schemas.manga_blacklist import BlackListManga, BlackListMangaCreate
from src.models import manga_blacklist as manga_blacklist_model
from src.schemas.general import Pagination, IntId
from src.db import get_db
from asyncpg import Connection


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/", status_code=status.HTTP_200_OK, response_model=Pagination[BlackListManga])
async def get_mangas_in_blacklist(
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
) -> Pagination[BlackListManga]:
    return await manga_blacklist_model.get_mangas_in_blacklist(limit, offset, conn)
    

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=BlackListManga)
async def add_manga_to_blacklist(blacklist_manga: BlackListMangaCreate, conn: Connection = Depends(get_db)) -> BlackListManga:
    return await manga_blacklist_model.add_manga_to_blacklist(blacklist_manga, conn)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def remove_manga_from_blacklist(manga: IntId, conn: Connection = Depends(get_db)):
    await manga_blacklist_model.remove_manga_from_blacklist(manga, conn)