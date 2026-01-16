from src.schemas.user import (
    User, 
    UserLogin, 
    UserLoginData, 
    UserCreate, 
    UserSession
)
from fastapi import APIRouter, Depends, status, Request, Cookie, Query
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import HTTPException
from src.schemas.token import SessionToken
from src.security import get_user_from_token
from src.schemas.general import Pagination, Exists
from src.models import user as user_model
from src.db import get_db
from datetime import datetime, timezone, timedelta
from src.constants import Constants
from asyncpg import Connection, UniqueViolationError
from typing import Optional
from src import security
from src import util



router = APIRouter()


@router.get("/me", status_code=status.HTTP_200_OK, response_model=User)
async def get_me(user: User = Depends(get_user_from_token)):
    return user


@router.post("/login", status_code=status.HTTP_200_OK, response_model=User)
async def login(
    user_login: UserLogin,
    request: Request,
    conn: Connection = Depends(get_db)
):
    user_login_data: Optional[UserLoginData] = await user_model.get_user_login_data(
        user_login,
        conn
    )
    
    if user_login_data is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        
    if Constants.IS_PRODUCTION and user_login_data.locked_until and user_login_data.locked_until > datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Account locked until {user_login_data.locked_until}")
    
    print(user_login.password, user_login_data.p_hash)
    
    if not security.verify_password(user_login.password, user_login_data.p_hash):
        user_login_data = await user_model.register_failed_login_attempt(user_login_data, conn)
        if user_login_data.login_attempts >= Constants.LOGIN_MAX_FAILED_ATTEMPTS:
            user_login_data.locked_until = datetime.now(timezone.utc) + timedelta(minutes=Constants.LOCK_TIME_MINUTES)
            await user_model.lock_user_login(user_login_data, conn)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Account locked until {user_login_data.locked_until}")
                
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    await user_model.reset_user_login_attempts(user_login_data, conn)
    
    # Create unique access token
    session_token: SessionToken = security.create_session_token(user_login_data.id)
    await user_model.create_user_session_token(
        user_login_data.id,
        session_token.refresh_token,
        util.get_client_info(request),
        conn
    )

    await user_model.update_user_last_login_at(user_login_data.id, conn)
    
    user = User(
        id=user_login_data.id,
        username=user_login_data.username,
        perfil_image_url=user_login_data.perfil_image_url,
        email=user_login_data.email,
        last_login_at=user_login_data.last_login_at,
        created_at=user_login_data.created_at
    )
    response = JSONResponse(content=user.model_dump(mode='json'))
    security.set_session_token_cookie(response, session_token)
    
    return response


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(new_user: UserCreate, conn: Connection = Depends(get_db)):
    try:
        hashed_password: bytes = security.hash_password(new_user.password)
        await user_model.create_user(new_user, hashed_password, conn)
        return Response(status_code=status.HTTP_201_CREATED)
    except UniqueViolationError as e:
        if 'username' in str(e):
            raise HTTPException(status_code=409, detail="Username already registered")
        raise HTTPException(status_code=409, detail="Email already registered")


@router.get("/sessions", response_model=Pagination[UserSession])
async def get_manager_active_sessions(
    limit: int = Query(default=64, le=64, ge=1),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_user_from_token),
    conn: Connection = Depends(get_db)
):
    return await user_model.get_user_sessions(user, limit, offset, conn)


@router.post("/refresh", response_model=User)
async def refresh_token_manager(
    response: Response,
    refresh_token: Optional[str] = Cookie(default=None), 
    conn: Connection = Depends(get_db)
):
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    
    user: Optional[User] = await user_model.get_user_by_refresh_token(refresh_token, conn)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    
    session_token: SessionToken = security.create_session_token(user.id)
    session_token.refresh_token.token = refresh_token

    await user_model.update_user_session_token(
        user.id,
        session_token.refresh_token,
        conn 
    )

    user: User = await user_model.get_user(user.id, conn)
    security.set_session_token_cookie(response, session_token)
    return user


@router.post("/logout")
async def logout(refresh_token: str | None = Cookie(default=None), conn: Connection = Depends(get_db)):
    if refresh_token is not None:
        await user_model.delete_user_session_token(refresh_token, conn)
    
    response = Response()
    security.unset_session_token_cookie(response)
    return response


@router.post("/logout/all")
async def logout(user: User = Depends(get_user_from_token), conn: Connection = Depends(get_db)):
    await user_model.delete_all_user_session_tokens(user.id, conn)
    response = Response()
    security.unset_session_token_cookie(response)
    return response


@router.get("/username/exists")
async def username_exists(
    username: str = Query(),
    conn: Connection = Depends(get_db)
):
    r: bool = await user_model.username_exists(username, conn)    
    return Exists(exists=r)


@router.get("/email/exists")
async def email_exists(
    email: str = Query(),
    conn: Connection = Depends(get_db)
):
    r: bool = await user_model.email_exists(email, conn)    
    return Exists(exists=r)