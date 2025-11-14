from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional


class Comment(BaseModel):

    id: int
    manga_id: int
    user_id: UUID
    comment: str
    parent_id: Optional[int]
    path: Optional[str]
    created_at: datetime
    total_replies: int


class CommentCreate(BaseModel):

    manga_id: int
    comment: str


class CommentReply(BaseModel):

    manga_id: int
    parent_id: int
    comment: str