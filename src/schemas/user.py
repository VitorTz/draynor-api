from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID
from typing import Optional


# Não enviar como resposta, apenas para uso local
class User(BaseModel):

    id: UUID
    username: str
    email: EmailStr
    p_hash: bytes
    perfil_image_url: Optional[str] = None
    created_at: datetime
    last_login_at: Optional[datetime] = None


class UserResponse(BaseModel):

    id: UUID
    username: str
    email: EmailStr
    perfil_image_url: Optional[str] = None
    created_at: datetime
    last_login_at: Optional[datetime] = None