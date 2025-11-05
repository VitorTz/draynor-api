from asyncpg import Connection
from src.schemas.manga import Manga, MangaCreate, MangaUpdate
from src.schemas.general import Pagination, IntId
from src.db import db_count
from typing import Optional
from src.exceptions import DatabaseError


async def get_mangas(limit: int, offset: int, conn: Connection) -> Pagination[Manga]:
    total = await db_count('mangas', conn)
    rows = await conn.fetch(
        """
            SELECT
                id,
                title,
                descr,
                cover_image_url,
                status,
                color,
                updated_at,
                created_at,
                mal_url
            FROM
                mangas
            ORDER BY
                id ASC
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
        results=[Manga(**dict(row)) for row in rows]
    )


async def create_manga(manga: MangaCreate, conn: Connection) -> Manga:
    r = await conn.fetchrow(
        """
            SELECT
                id,
                title,
                descr,
                cover_image_url,
                status,
                color,
                updated_at,
                created_at,
                mal_url
            FROM
                mangas
            WHERE
                title = TRIM($1)
        """,
        manga.title
    )

    if not r:
        r = await conn.fetchrow(
            """
                INSERT INTO mangas (
                    title,
                    descr,
                    cover_image_url,
                    status,
                    color,
                    mal_url
                )
                VALUES (
                    TRIM($1),
                    TRIM($2),
                    $3,
                    $4,
                    $5,
                    $6
                )
                RETURNING
                    id,
                    title,
                    descr,
                    cover_image_url,
                    status,
                    color,
                    updated_at,
                    created_at,
                    mal_url
            """,
            manga.title,
            manga.descr,
            manga.cover_image_url,
            manga.status,
            manga.color,
            manga.mal_url
        )
    
    return Manga(**dict(r))


async def update_manga(manga: MangaUpdate, conn: Connection) -> Optional[Manga]:
    old_manga = await conn.fetchrow("SELECT * FROM mangas WHERE id = $1", manga.id)
    if not old_manga:
        raise DatabaseError(
            detail=f'manga with id {manga.id} not found',
            code=404
        )
    
    old_data = dict(old_manga)
    
    fields = ["title", "descr", "cover_image_url", "status", "color", "mal_url"]
    updated_data = {}
    for field in fields:
        value = getattr(manga, field, None)
        updated_data[field] = value if value else old_data[field]
    
    row = await conn.fetchrow(
        """
        UPDATE 
            mangas
        SET
            title = TRIM($1),
            descr = TRIM($2),
            cover_image_url = $3,
            status = $4,
            color = $5,
            mal_url = $6
        WHERE 
            id = $7
        RETURNING 
            id, 
            title, 
            descr, 
            cover_image_url, 
            status, 
            color, 
            updated_at, 
            created_at, 
            mal_url
        """,
        updated_data["title"],
        updated_data["descr"],
        updated_data["cover_image_url"],
        updated_data["status"],
        updated_data["color"],
        updated_data["mal_url"],
        manga.id
    )

    return Manga(**dict(row)) if row else None


async def delete_manga(manga: IntId, conn: Connection) -> None:
    await conn.execute("DELETE FROM mangas WHERE id = $1", manga.id)