from src.schemas.manga_request import MangaRequest, MangaRequestCreate
from src.schemas.general import Pagination, IntId
from src.security import require_admin
from fastapi import APIRouter, Depends, Query, status
from src.models import manga_request as manga_request_model
from src.db import get_db
from asyncpg import Connection
from typing import Optional, Literal


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/", status_code=status.HTTP_200_OK, response_model=Pagination[MangaRequest])
async def get_manga_requests(
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    order: Optional[Literal['ASC', 'DESC']] = Query(default='DESC'),
    conn: Connection = Depends(get_db)
) -> Pagination[MangaRequest]:
    return await manga_request_model.get_manga_requests(limit, offset, order, conn)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=MangaRequest)
async def get_manga_requests(
    manga_request: MangaRequestCreate,
    conn: Connection = Depends(get_db)
) -> MangaRequest:
    return await manga_request_model.create_manga_request(manga_request, conn)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def get_manga_requests(
    manga_request: IntId,
    conn: Connection = Depends(get_db)
):
    await manga_request_model.delete_manga_request(manga_request, conn)