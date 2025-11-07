from src.schemas.manga_request import MangaRequest, MangaRequestCreate
from src.schemas.general import Pagination, IntId
from asyncpg import Connection
from src.db import db_count


async def get_manga_requests(
    limit: int,
    offset: int,
    order: str,
    conn: Connection
):
    total: int = await db_count('manga_requests', conn)

    if order not in ('ASC', 'DESC'):
        order = 'DESC'
    
    rows = await conn.fetch(
        f"""
            SELECT
                if,
                title,
                message,
                created_at
            FROM
                manga_requests
            ORDER BY
                created_at {order}
            LIMIT
                $1
            OFFSET
                $2
        """,
        limit,
        offset
    )

    return Pagination(
        total=total,
        limit=limit,
        offset=offset,
        results=[MangaRequest(**dict(row)) for row in rows]
    )


async def create_manga_request(manga_request: MangaRequestCreate, conn: Connection) -> MangaRequest:
    row = await conn.fetchrow(
        """
            INSERT INTO manga_requests (
                title,
                message
            )
            VALUES
                ($1, $2)
            RETURNING
                id,
                title,
                message,
                created_at
        """,
        manga_request.title,
        manga_request.message
    )
    return MangaRequest(**dict(row))


async def delete_manga_request(manga_request: IntId, conn: Connection):
    await conn.execute(
        """
            DELETE FROM
                manga_requests
            WHERE
                id = $1
        """,
        manga_request.id
    )