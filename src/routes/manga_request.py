from src.schemas.manga_request import MangaRequest, MangaRequestCreate
from fastapi import APIRouter, Depends, status
from src.models import manga_request as manga_request_model
from src.db import get_db
from asyncpg import Connection


router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=MangaRequest)
async def get_manga_requests(
    manga_request: MangaRequestCreate,
    conn: Connection = Depends(get_db)
) -> MangaRequest:
    return await manga_request_model.create_manga_request(manga_request, conn)
