from fastapi import Depends, HTTPException, status, Cookie, Response
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
from src.models import user as user_model
from src.schemas.user import User, UserLoginAttempt
from src.schemas.token import SessionToken, Token
from src.constants import Constants
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from asyncpg import Connection
from typing import Optional
from src.db import get_db
from src import util
import uuid
import jwt


oauth2_admin_scheme = OAuth2PasswordBearer(tokenUrl="/admin/login")


ph = PasswordHasher()


CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def create_admin_token():
    payload = {
        "sub": "admin",
        "exp": datetime.now(timezone.utc) + timedelta(hours=24)
    }
    return jwt.encode(payload, Constants.SECRET_KEY, algorithm=Constants.ALGORITHM)


def check_admin_token(token: Optional[str]):
    if not token: return False
    try:
        payload = jwt.decode(token, Constants.SECRET_KEY, algorithms=[Constants.ALGORITHM])
        if payload.get("sub") != "admin": return False
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False
    return True


def require_admin(token: str = Depends(oauth2_admin_scheme)):
    if not check_admin_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized access"
        )
    return True


def hash_password(password: str) -> bytes:
    hashed_str = ph.hash(password)
    return hashed_str.encode('utf-8')


def verify_password(plain_password: str, hashed_password: bytes) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False
    

def create_new_refresh_token_expires_time() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=Constants.REFRESH_TOKEN_EXPIRE_DAYS)


def create_new_access_token_expires_time() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=Constants.ACCESS_TOKEN_EXPIRE_MINUTES)


def create_refresh_token() -> Token:
    return Token(
        token=str(uuid.uuid4()), 
        expires_at=create_new_refresh_token_expires_time()
    )


def create_access_token(manager_id: uuid.UUID) -> Token:
    expires_at: str = datetime.now(timezone.utc) + (timedelta(minutes=Constants.ACCESS_TOKEN_EXPIRE_MINUTES))
    data = {
        "sub": str(manager_id), 
        "exp": expires_at
    }
    token: str = jwt.encode(
        data,
        Constants.SECRET_KEY,
        algorithm=Constants.ALGORITHM
    )
    return Token(token=token, expires_at=expires_at)


def create_session_token(manager_id: uuid.UUID) -> SessionToken:
    return SessionToken(
        access_token=create_access_token(manager_id), 
        refresh_token=create_refresh_token()
    )


def check_user_login_attempts(lock: UserLoginAttempt):
    now = datetime.now(timezone.utc)
    if lock.locked_until and lock.locked_until > now:
        raise HTTPException(status_code=403, detail=f"Account locked until {lock.locked_until}")
    

async def get_user_from_token(
    access_token: Optional[str] = Cookie(default=None),
    conn: Connection = Depends(get_db)
) -> User:
    if access_token is None: 
        raise CREDENTIALS_EXCEPTION
    
    try:
        payload = jwt.decode(
            access_token,
            Constants.SECRET_KEY,
            algorithms=[Constants.ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None: 
            raise CREDENTIALS_EXCEPTION
    except Exception:
        raise CREDENTIALS_EXCEPTION
    
    user: Optional[User] = await user_model.get_user(user_id, conn)
    
    if user is None:
        raise CREDENTIALS_EXCEPTION
    
    return user


async def require_user_login(access_token: Optional[str] = Cookie(default=None)):
    if access_token is None: 
        raise CREDENTIALS_EXCEPTION
    
    try:
        payload = jwt.decode(
            access_token,
            Constants.SECRET_KEY,
            algorithms=[Constants.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None: 
            raise CREDENTIALS_EXCEPTION
    except Exception:
        raise CREDENTIALS_EXCEPTION
    
    if not await user_model.user_exists(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


async def get_user_from_token_if_exists(
    access_token: Optional[str] = Cookie(default=None),
    conn: Connection = Depends(get_db)
) -> Optional[User]:
    if access_token is None: return None

    try:
        payload = jwt.decode(
            access_token,
            Constants.SECRET_KEY,
            algorithms=[Constants.ALGORITHM]
        )
        user_id: str | None = payload.get("sub")
        if user_id: return await user_model.get_user(user_id, conn)
    except Exception:
        return None
    

def set_session_token_cookie(response: Response, session_token: SessionToken):
    if Constants.IS_PRODUCTION:
        samesite_policy = "none"
        secure_policy = True
    else:
        samesite_policy = "lax"
        secure_policy = False
    
    response.set_cookie(
        key="refresh_token",
        value=session_token.refresh_token.token,
        httponly=True,
        secure=secure_policy,
        samesite=samesite_policy,
        path="/",
        max_age=util.seconds_until(session_token.refresh_token.expires_at)
    )

    response.set_cookie(
        key="access_token",
        value=session_token.access_token.token,
        httponly=True,
        secure=secure_policy,
        samesite=samesite_policy,
        path="/",
        max_age=util.seconds_until(session_token.access_token.expires_at)
    )


def unset_session_token_cookie(response: Response):
    if Constants.IS_PRODUCTION:
        samesite_policy = "none"
        secure_policy = True 
    else:
        samesite_policy = "lax"
        secure_policy = False

    response.delete_cookie(
        key="access_token", 
        httponly=True, 
        path='/', 
        samesite=samesite_policy, 
        secure=secure_policy
    )

    response.delete_cookie(
        key="refresh_token", 
        httponly=True, 
        path='/', 
        samesite=samesite_policy, 
        secure=secure_policy
    )