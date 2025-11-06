from asyncpg import Connection
from src.schemas.manga import Manga, MangaCreate, MangaUpdate
from src.schemas.general import Pagination, IntId
from src.db import db_count
from typing import Optional
from src.exceptions import DatabaseError


async def get_mangas(
    limit: int,
    offset: int,
    conn: Connection,
    q: Optional[str] = None,
    title: Optional[str] = None
) -> Pagination[Manga]:
    base_query = """
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
        FROM mangas
    """

    conditions = []
    params = []
    if q:
        conditions.append("title ILIKE $1")
        params.append(f"%{q}%")
    elif title:
        conditions.append("title = $1")
        params.append(title)

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)
        total_query = f"SELECT COUNT(*) FROM mangas {where_clause}"
        total = await conn.fetchval(total_query, *params)
        query = f"{base_query} {where_clause} ORDER BY id ASC LIMIT ${len(params)+1} OFFSET ${len(params)+2}"
        rows = await conn.fetch(query, *params, limit, offset)
    else:
        total = await db_count('mangas', conn)
        query = f"{base_query} ORDER BY id ASC LIMIT $1 OFFSET $2"
        rows = await conn.fetch(query, limit, offset)

    return Pagination(
        total=total,
        limit=limit,
        offset=offset,
        results=[Manga(**dict(r)) for r in rows]
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