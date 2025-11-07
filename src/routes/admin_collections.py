from src.schemas.collection import (
    Collection, 
    CollectionCreate,
    CollectionUpdate,
    CollectionMangaCreate,
    CollectionMangaDelete
)
from fastapi import APIRouter, Depends, Query, status
from src.schemas.general import Pagination, IntId
from src.schemas.manga import Manga
from src.models import collection as collection_model
from src.security import require_admin
from src.db import get_db
from asyncpg import Connection


router = APIRouter(dependencies=[Depends(require_admin)])



@router.get("/", status_code=status.HTTP_200_OK, response_model=Pagination[Collection])
async def get_collections(
    limit: int = Query(default=64, get=0, le=64),
    offset: int = Query(default=0, get=0),
    conn: Connection = Depends(get_db)
) -> Pagination[Collection]:
    return await collection_model.get_collections(limit, offset, conn)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Collection)
async def create_collection(
    collection: CollectionCreate, 
    conn: Connection = Depends(get_db)
) -> Collection:
    return await collection_model.create_collection(collection, conn)


@router.put("/", status_code=status.HTTP_201_CREATED, response_model=Collection)
async def update_collection(
    collection: CollectionUpdate, 
    conn: Connection = Depends(get_db)
) -> Collection:
    return await collection_model.update_collection(collection, conn)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(collection: IntId, conn: Connection = Depends(get_db)):
    await collection_model.delete_collection(collection, conn)



@router.get("/mangas", status_code=status.HTTP_200_OK, response_model=Pagination[Manga])
async def get_mangas_from_collection(
    collection: IntId, 
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
) -> Pagination[Manga]:
    return collection_model.get_mangas_from_collection(collection, limit, offset, conn)


@router.post("/mangas", status_code=status.HTTP_200_OK)
async def add_manga_to_collection(
    collection_manga: CollectionMangaCreate,
    conn: Connection = Depends(get_db)
):
    await collection_model.add_manga_to_collection(collection_manga, conn)


@router.delete("/mangas", status_code=status.HTTP_204_NO_CONTENT)
async def remove_manga_from_collection(
    collection_manga: CollectionMangaDelete,
    conn: Connection = Depends(get_db)
):
    await collection_model.remove_manga_from_collection(collection_manga, conn)