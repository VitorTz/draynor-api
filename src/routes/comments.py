from src.schemas.comments import Comment, CommentCreate, CommentReply
from fastapi import APIRouter, Depends, status, Query
from src.schemas.general import IntId, Pagination
from src.schemas.user import User
from src.models import comments as comments_model
from src.security import get_user_from_token
from asyncpg import Connection
from src.db import get_db


router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Comment)
async def create_comment(
    comment: CommentCreate,
    user: User = Depends(get_user_from_token),
    conn: Connection = Depends(get_db)
) -> Comment:
    return await comments_model.create_comment(comment, user, conn)


@router.post("/reply", status_code=status.HTTP_201_CREATED, response_model=Comment)
async def reply(
    comment: CommentReply, 
    user: User = Depends(get_user_from_token),
    conn: Connection = Depends(get_db)
) -> Comment:
    return await comments_model.reply_comment(comment, user, conn)


@router.get("/manga", status_code=status.HTTP_200_OK, response_model=Pagination[Comment])
async def get_comments_from_manga(
    manga_id: int = Query(...),
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
) -> Pagination[Comment]:
    return await comments_model.get_manga_root_comments(manga_id, limit, offset, conn)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment: IntId,
    user: User = Depends(get_user_from_token),
    conn: Connection = Depends(get_db)
) -> None:
    await comments_model.delete_comment(comment.id, user, conn)