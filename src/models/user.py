from src.schemas.user import (
    User, 
    UserLogin, 
    UserLoginData, 
    UserCreate,
    UserSession, 
    UserUpdate
)
from src.schemas.token import Token
from src.schemas.general import ClientInfo, Pagination
from asyncpg import Connection
from src.exceptions import DatabaseError
from typing import Optional


async def user_exists(user_id: str, conn: Connection) -> bool:
    r = await conn.fetchval("SELECT id FROM users WHERE id = $1", user_id)
    return r is not None


async def get_user(user_id: str, conn: Connection) -> Optional[User]:
    r = await conn.fetchrow(
        """
            SELECT
                id,
                username,
                email,
                perfil_image_url,
                last_login_at,
                created_at
            FROM
                users
            WHERE
                id = $1
        """,
        user_id
    )

    return User(**dict(r)) if r else None


async def get_user_login_data(login: UserLogin, conn: Connection) -> Optional[UserLoginData]:
    r = await conn.fetchrow(
        """
            SELECT
                u.id,
                u.username,
                u.perfil_image_url,
                u.email,
                u.p_hash,
                u.created_at,
                u.last_login_at,
                ul.attempts as login_attempts,
                ul.last_failed_login,
                ul.locked_until
            FROM
                users u
            JOIN
                user_login_attempts ul ON ul.user_id = u.id
            WHERE
                email = TRIM($1)
        """,
        login.email
    )

    return UserLoginData(**dict(r)) if r else None


async def register_failed_login_attempt(user_login_data: UserLoginData, conn: Connection) -> UserLoginData:
    await conn.execute(
        """
            UPDATE 
                user_login_attempts
            SET
                attempts = attempts + 1,
                last_failed_login = CURRENT_TIMESTAMP,
                locked_until = $1
            WHERE
                user_id = $2
        """,
        user_login_data.locked_until,
        user_login_data.id
    )
    user_login_data.login_attempts += 1
    return user_login_data


async def lock_user_login(user_login_data: UserLoginData, conn: Connection):
    await conn.execute(
        """
            UPDATE 
                user_login_attempts
            SET
                locked_until = $1
            WHERE
                user_id = $2
        """,
        user_login_data.locked_until,
        user_login_data.id
    )


async def reset_user_login_attempts(user_login_data: UserLoginData, conn: Connection):
    await conn.execute(
        """
            UPDATE 
                user_login_attempts
            SET
                attempts = 0,
                last_failed_login = NULL,
                locked_until = NULL,
                last_successful_login = CURRENT_TIMESTAMP
            WHERE
                user_id = $1
        """,
        user_login_data.id
    )


async def create_user_session_token(
    user_id: str,
    token: Token,
    client_info: ClientInfo,
    conn: Connection
) -> None:
    await conn.execute(
        """
            INSERT INTO user_session_tokens (
                user_id,
                refresh_token,
                expires_at,
                device_name,
                device_ip,
                user_agent
            )
            VALUES 
                ($1, $2, $3, COALESCE($4, 'unknown'), $5, $6)
            ON CONFLICT
                (user_id, device_ip, user_agent)
            DO UPDATE SET
                refresh_token = EXCLUDED.refresh_token,
                expires_at = EXCLUDED.expires_at,
                device_name = EXCLUDED.device_name,
                last_used_at = CURRENT_TIMESTAMP
        """,
        user_id, 
        token.token, 
        token.expires_at,
        client_info.device_name,
        client_info.client_ip,
        client_info.user_agent
    )


async def update_user_last_login_at(user_id: str, conn: Connection):
    await conn.execute(
        """
            UPDATE 
                users
            SET
                last_login_at = NOW()
            WHERE
                id = $1
        """,
        user_id
    )



async def create_user(new_user: UserCreate, conn: Connection) -> User:
    r = await conn.fetchrow(
        """
            INSERT INTO users (
                username,
                email,
                p_hash
            )
            VALUES  
                ($1, LOWER(TRIM($2)), decode(md5(TRIM($3)), 'hex'))
            RETURNING
                id,
                username,
                perfil_image_url,
                email,
                last_login_at,
                created_at
        """,
        new_user.username,
        new_user.email,
        new_user.password
    )

    return User(**dict(r)) if r else None


async def delete_user_session_token(refresh_token: str, conn: Connection):
    await conn.execute(
        """
            DELETE FROM 
                user_session_tokens
            WHERE
                refresh_token = $1
        """,        
        refresh_token
    )

async def delete_all_user_session_tokens(user_id: str, conn: Connection):
    await conn.execute(
        """
            DELETE FROM 
                user_session_tokens
            WHERE
                user_id = $1
        """,        
        user_id
    )


async def get_user_by_refresh_token(refresh_token: str, conn: Connection) -> Optional[User]:
    r = await conn.fetchrow(
        """
            SELECT 
                u.id,
                u.usermame,
                u.email,
                u.last_login_at,
                u.created_at
            FROM 
                users u
            JOIN 
                user_session_tokens rt ON rt.user_id = u.id
            WHERE 
                rt.refresh_token = $1;
        """,
        refresh_token
    )
    return User(**dict(r)) if r else None


async def update_user_session_token(
    user_id: str,
    refresh_token: Token,
    conn: Connection
):    
    await conn.execute(
        """
            UPDATE
                user_session_tokens
            SET
                expires_at = $1,
                revoked = $2,
                revoked_at = $3,
                last_used_at = CURRENT_TIMESTAMP
            WHERE
                user_id = $4 AND
                refresh_token = $5
        """,
        refresh_token.expires_at,
        refresh_token.revoked,
        refresh_token.revoked_at,
        user_id,
        refresh_token.token
    )

async def get_user_sessions(user: User, limit: int, offset: int, conn: Connection):
    total: int = await conn.fetchval(
        "SELECT COUNT(*) AS total FROM user_session_tokens WHERE user_id = $1", 
        user.id
    )

    r = await conn.fetch(
        """
            SELECT
                user_id,
                issued_at,
                expires_at,
                revoked,
                revoked_at,
                device_name,
                device_ip,
                user_agent,
                last_used_at
            FROM
                user_session_tokens
            WHERE
                user_id = $1
            ORDER BY
                issued_at DESC
            LIMIT
                $2
            OFFSET
                $3
        """,
        user.id,
        limit,
        offset
    )

    return Pagination[UserSession](
        total=total,
        limit=limit,
        offset=offset,
        results=[UserSession(**dict(i)) for i in r]
    )


async def update_user(old_user: User, user: UserUpdate, conn: Connection) -> User:
    row = await conn.fetchrow(
        """
            UPDATE 
                users
            SET
                username = TRIM(COALESCE($1, $2)),
                email = TRIM(COALESCE($3, $4))
            WHERE 
                id = $5
            RETURNING
                id,
                username,
                email,
                perfil_image_url,
                created_at,
                last_login_at
        """,
        user.username, old_user.username,
        user.email, old_user.email,
        old_user.id
    )

    return User(**dict(row))


async def update_user_perfil_image_urll(user: User, perfil_image_url: Optional[str], conn: Connection) -> User:
    await conn.execute(
        """
            UPDATE
                users
            SET
                perfil_image_url = $1
            WHERE
                id = $2
        """,
        perfil_image_url,
        user.id
    )

    user.perfil_image_url = perfil_image_url
    return user


async def username_exists(username: str, conn: Connection) -> bool:
    r = await conn.fetchval(
        "SELECT id FROM users WHERE TRIM(LOWER(username)) = TRIM(LOWER($1))", 
        username
    )
    return r is not None


async def email_exists(email: str, conn: Connection) -> bool:
    r = await conn.fetchval(
        "SELECT id FROM users WHERE TRIM(LOWER(email)) = TRIM(LOWER($1))", 
        email
    )
    return r is not None