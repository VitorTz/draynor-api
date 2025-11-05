from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from src.constants import Constants


oauth2_admin_scheme = OAuth2PasswordBearer(tokenUrl="/admin/login")


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
