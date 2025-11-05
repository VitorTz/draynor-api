from fastapi import APIRouter, Depends, Query, status
from src.security import require_admin
from src.schemas.log import Log, LogStats, DeletedLogs
from src.schemas.general import Pagination
from src.db import get_db
from src.models import log as log_model
from typing import Optional, Literal
from asyncpg import Connection


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/", status_code=status.HTTP_200_OK, response_model=Pagination[Log])
async def get_logs(
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await log_model.get_logs(limit, offset, conn)


@router.get("/stats", status_code=status.HTTP_200_OK, response_model=LogStats)
async def get_log_stats(
    conn: Connection = Depends(get_db)
):
    return await log_model.get_log_stats(conn)


@router.delete("/", status_code=status.HTTP_200_OK, response_model=DeletedLogs)
async def delete_logs(
    interval_minutes: Optional[int] = Query(default=None),
    method: Optional[Literal['GET', 'PUT', 'POST', 'DELETE']] = Query(default=None),
    conn: Connection = Depends(get_db)
):
    return await log_model.delete_logs(interval_minutes, method, conn)


