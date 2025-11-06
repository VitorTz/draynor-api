from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Token(BaseModel):
    
    token: str    
    expires_at: datetime
    revoked: Optional[bool] = False
    revoked_at: Optional[datetime] = None


class SessionToken(BaseModel):
    
    access_token: Token
    refresh_token: Token