from pydantic import BaseModel, EmailStr, IPvAnyAddress
from datetime import datetime
from uuid import UUID
from typing import Optional


class User(BaseModel):

    id: UUID
    username: str
    email: EmailStr
    created_at: datetime
    perfil_image_url: Optional[str] = None
    last_login_at: Optional[datetime] = None


class UserLogin(BaseModel):

    email: EmailStr
    password: str


class UserCreate(BaseModel):

    username: str
    email: EmailStr
    password: str
    perfil_image_url: Optional[str] = None


class UserUpdate(BaseModel):

    username: Optional[str] = None
    email: Optional[EmailStr] = None

class UserLoginAttempt(BaseModel):

    user_id: str
    attempts: int
    last_failed_login: Optional[datetime]
    locked_until: Optional[datetime]


class UserLoginData(BaseModel):

    id: UUID
    username: str
    email: str
    p_hash: bytes
    login_attempts: int
    perfil_image_url: Optional[str] = None
    last_login_at: Optional[datetime] = None
    last_failed_login: Optional[datetime] = None
    locked_until: Optional[datetime] = None
    created_at: datetime


class UserSession(BaseModel):

    user_id: UUID
    issued_at: datetime
    expires_at: datetime
    revoked: bool
    revoked_at: Optional[datetime] = None
    device_name: Optional[str] = None
    device_ip: IPvAnyAddress
    user_agent: Optional[str] = None
    last_used_at: datetime