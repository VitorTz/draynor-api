from src.schemas.manga_blacklist import BlackListMangaCreate, BlackListManga
from src.schemas.general import Pagination, IntId
from asyncpg import Connection
from src.db import db_count


async def get_mangas_in_blacklist(
    limit: int,
    offset: int,
    conn: Connection
) -> Pagination[BlackListManga]:
    total: int = await db_count("manga_blacklist", conn)
    rows = await conn.fetch(
        """
            SELECT
                manga_id,
                descr,
                created_at
            FROM
                manga_blacklist
            ORDER BY
                created_at DESC
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
        results=[BlackListManga(**dict(row)) for row in rows]
    )


async def add_manga_to_blacklist(blacklist_manga: BlackListMangaCreate, conn: Connection):
    row = await conn.execute(
        """
            INSERT INTO manga_blacklist (
                manga_id,
                descr
            )
            VALUES
                ($1, $2)
            ON CONFLICT
                (manga_id)
            DO UPDATE SET
                descr = EXCLUDED.descr
            RETURNING
                manga_id,
                descr,
                created_at
        """,
        blacklist_manga.manga_id,
        blacklist_manga.descr
    )

    return BlackListManga(**dict(row))


async def remove_manga_from_blacklist(manga: IntId, conn: Connection):
    await conn.execute(
        """
            DELETE FROM
                manga_blacklist
            WHERE
                manga_id = $1
        """,
        manga.id
    )