from fastapi import APIRouter, Depends, status, Query
from src.models import collection as collection_model
from src.schemas.general import Pagination, IntId
from src.schemas.collection import Collection
from src.schemas.manga import Manga
from src.db import get_db
from asyncpg import Connection


router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK, response_model=Pagination[Collection])
async def get_collections(
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
) -> Pagination[Collection]:
    return await collection_model.get_collections(limit, offset, conn)


@router.get("/mangas", status_code=status.HTTP_200_OK, response_model=Pagination[Manga])
async def get_mangas_from_collection(
    collection: IntId,
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await collection_model.get_mangas_from_collection(collection, limit, offset, conn)