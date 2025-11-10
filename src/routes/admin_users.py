from fastapi import APIRouter, Depends, Query, status
from src.security import require_admin
from src.schemas.user import User
from src.models import user as user_model
from src.schemas.general import Pagination, StrId
from src.db import get_db
from asyncpg import Connection


router = APIRouter(dependencies=[Depends(require_admin)])



@router.get("/", status_code=status.HTTP_200_OK, response_model=Pagination[User])
async def get_users(
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
) -> Pagination[User]:
    return await user_model.get_users(limit, offset, conn)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user: StrId, conn: Connection = Depends(get_db)):
    await user_model.delete_user(user.id, conn)