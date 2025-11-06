from src.schemas.reading_status import (
    ReadingStatusCreate, 
    ReadingStatusLiteral, 
    DeleteReadingStatus, 
    MangaReadingStatus
)
from src.schemas.general import Pagination, IntId
from src.schemas.manga import Manga
from src.schemas.user import User
from asyncpg import Connection


async def upsert_reading_status(reading_status: ReadingStatusCreate, user: User, conn: Connection) -> None:
    await conn.execute(
        """
            INSERT INTO library (
                manga_id,
                user_id,
                reading_status
            )
            VALUES
                ($1, $2, TRIM($3)::reading_status_enum)
            ON CONFLICT
                (manga_id, user_id)
            DO UPDATE SET
                reading_status = EXCLUDED.reading_status,
                updated_at = CURRENT_TIMESTAMP
        """,
        reading_status.manga_id,
        user.id,
        reading_status.reading_status
    )


async def get_manga_reading_status(manga: IntId, user: User, conn: Connection):
    row = await conn.fetchrow(
        """
            SELECT
                id,
                manga_id,
                user_id,
                reading_status,
                created_at,
                updated_at
            FROM
                library
            WHERE
                manga_id = $1
                AND user_id = $2
        """,
        manga.id,
        user.id
    )

    return MangaReadingStatus(**dict(row)) if row else None


async def get_mangas_by_reading_status(
    reading_status: ReadingStatusLiteral, 
    user: User,
    limit: int,
    offset: int,
    conn: Connection
) -> Pagination[Manga]:
    total = await conn.fetchval(
        """
            SELECT
                COUNT(m.*)
            FROM
                library ul
            JOIN
                mangas m ON m.manga_id = ul.manga_id
            WHERE
                ul.reading_status = $1
                AND ul.user_id = $2
        """,
        reading_status,
        user.id
    )
    rows = await conn.fetch(
        """
            SELECT
                m.id,
                m.title,
                m.descr,
                m.status,
                m.color,
                m.cover_image_url,
                m.created_at,
                m.updated_at,
                m.mal_url
            FROM
                library ul
            JOIN
                mangas m ON m.manga_id = ul.manga_id
            WHERE
                ul.reading_status = $1
                ul.user_id = $2
            ORDER BY
                ul.updated_at DESC
            LIMIT
                $3
            OFFSET
                $4

        """,
        reading_status,
        user.id,
        limit,
        offset
    )

    return Pagination(
        total=total,
        limit=limit,
        offset=offset,
        results=[Manga(**dict(row)) for row in rows]
    )


async def delete_reading_status(reading_status: DeleteReadingStatus, user: User, conn: Connection) -> None:
    await conn.execute(
        """
            DELETE FROM
                library
            WHERE
                manga_id = $1
                AND user_id = $2
        """,
        reading_status.manga_id,
        user.id
    )