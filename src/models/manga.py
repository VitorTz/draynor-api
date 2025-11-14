from asyncpg import Connection
from src.schemas.manga import Manga, MangaCreate, MangaUpdate
from src.schemas.general import Pagination, IntId
from src.schemas.genre import Genre
from src.schemas.manga_page import MangaPageData, MangaPageChapter, MangaCarouselItem
from src.schemas.user import User
from src.schemas.author import MangaAuthor
from src.db import db_count
from typing import Optional, Literal
from src.exceptions import DatabaseError
import json


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


async def get_mangas_complete(
    title: Optional[str],
    genre_id: Optional[int],
    order: Literal['ASC', 'DESC'],
    limit: int,
    offset: int,
    conn: Connection
) -> Pagination[Manga]:
    
    if order not in ('ASC', 'DESC'):
        order = 'ASC'

    conditions = []
    params = []
    
    if title:
        params.append(f"%{title}%")
        conditions.append("m.title ILIKE $1")

    if genre_id:
        params.append(genre_id)
        conditions.append(f"mg.genre_id = ${len(params)}")

    base_query = """
            SELECT DISTINCT
                id,
                title,
                descr,
                status,
                color,
                cover_image_url,
                mal_url,
                updated_at,
                created_at
            FROM
                mangas m
            JOIN
                manga_genres mg ON mg.manga_id = m.id
        """
    
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)
        total_query = f"SELECT COUNT(DISTINCT (m.*)) FROM mangas m JOIN manga_genres mg ON mg.manga_id = m.id {where_clause};"
        total = await conn.fetchval(total_query, *params)
        query = f"{base_query} {where_clause} ORDER BY m.title {order} LIMIT ${len(params)+1} OFFSET ${len(params)+2}"
        rows = await conn.fetch(query, *params, limit, offset)
    else:
        total = await db_count('mangas', conn)
        query = f"{base_query} ORDER BY m.title {order} LIMIT $1 OFFSET $2"
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


async def get_popular_mangas(
    limit: int,
    offset: int,
    conn: Connection
):
    total: int = await db_count("mangas", conn)
    
    rows = await conn.fetch(
        """
           SELECT 
                m.id,
                m.title,
                m.descr,
                m.cover_image_url,
                m.status,
                m.color,
                m.updated_at,
                m.created_at,
                m.mal_url
            FROM 
                mangas m
            JOIN 
                manga_metrics mm ON mm.manga_id = m.id
            ORDER BY 
                mm.total_reads DESC, m.title ASC
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


async def get_latest_mangas(
    limit: int,
    offset: int,
    conn: Connection
) -> Pagination[Manga]:
    total: int = await db_count('mangas', conn)
    rows = await conn.fetch(
        """
            SELECT
                id,
                title,
                descr,
                status,
                cover_image_url,
                mal_url,
                color,
                updated_at,
                created_at
            FROM
                mangas
            ORDER BY
                updated_at DESC
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


async def get_random_mangas(
    limit: int,
    conn: Connection
) -> Pagination[Manga]:
    total = await db_count('mangas', conn)
    rows = await conn.fetch(
        """
            SELECT
                id,
                title,
                descr,
                status,
                cover_image_url,
                mal_url,
                color,
                updated_at,
                created_at
            FROM
                mangas
            ORDER BY
                RANDOM()
            LIMIT
                $1
        """,
        limit
    )

    return Pagination(
        total=total,
        limit=limit,
        offset=0,
        results=[Manga(**dict(row)) for row in rows]
    )


async def get_manga_by_genre(
    genre_id: int,
    limit: int,
    offset: int,
    conn: Connection
) -> Pagination[Manga]:
    rows = await conn.fetch(
        """
        SELECT
            m.id,
            m.title,
            m.descr,
            m.status,
            m.color,
            m.cover_image_url,
            m.mal_url,
            m.updated_at,
            m.created_at,
            COUNT(*) OVER() AS total_count
        FROM 
            mangas m
        JOIN 
            manga_genres mg ON mg.manga_id = m.id
        JOIN 
            manga_metrics mm ON mm.manga_id = m.id
        WHERE 
            mg.genre_id = $1
        ORDER BY 
            mm.total_reads DESC, m.title ASC
        LIMIT 
            $2 
        OFFSET 
            $3
        """,
        genre_id,
        limit,
        offset
    )

    if not rows:
        return Pagination(
            total=0, 
            limit=limit, 
            offset=offset, 
            results=[]
        )

    return Pagination(
        total=rows[0]["total_count"],
        limit=limit,
        offset=offset,
        results=[Manga(**dict(row)) for row in rows]
    )


async def update_cover_image_url(manga_id: int, cover_image_url: str, conn: Connection):
    await conn.execute(
        """
            UPDATE
                mangas
            SET
                cover_image_url = $1
            WHERE
                id = $2
        """,
        cover_image_url,
        manga_id
    )


async def get_manga_page_data(manga_id: int, user: Optional[User], conn: Connection) -> MangaPageData:
    row = await conn.fetchrow(
        "SELECT * FROM manga_page_view WHERE id = $1;",
        manga_id
    )

    if not row:
        raise DatabaseError(f"manga with id {manga_id} has no data", code=404)
    
    await conn.execute(
        """
            UPDATE
                manga_metrics
            SET
                total_reads = total_reads + 1
            WHERE
                manga_id = $1
        """,
        manga_id
    )

    chapters = json.loads(row['chapters'])
    genres = json.loads(row['genres'])
    authors = json.loads(row['authors'])

    if user:
        reading_status: Optional[str] = await conn.fetchval(
            """
                SELECT 
                    reading_status
                FROM 
                    library
                WHERE
                    manga_id = $1 AND user_id = $2
            """,
            manga_id,
            user.id
        )
    else:
        reading_status = None
    
    manga = Manga(
        id=row['id'],
        title=row['title'],
        descr=row['descr'],
        status=row['status'],
        color=row['color'],
        cover_image_url=row['cover_image_url'],
        mal_url=row['mal_url'],
        updated_at=row['updated_at'],
        created_at=row['created_at']
    )

    return MangaPageData(
        manga=manga,
        manga_num_views=row['views'] + 1,
        chapters=[MangaPageChapter(**dict(row)) for row in chapters],
        genres=[Genre(**dict(row)) for row in genres],
        authors=[MangaAuthor(**dict(row)) for row in authors],
        reading_status=reading_status
    )


async def get_mangas_page_data(limit: int, offset: int, conn: Connection) -> Pagination[MangaPageData]:
    total: int = await db_count("manga_page_view", conn)

    rows = await conn.fetch(
        """
            SELECT
                *
            FROM
                manga_page_view
            ORDER BY
                RANDOM()
            LIMIT
                $1
            OFFSET
                $2
        """,
        limit,
        offset
    )

    results = []

    for row in rows:
        manga = Manga(
            id=row['id'],
            title=row['title'],
            descr=row['descr'],
            status=row['status'],
            color=row['color'],
            cover_image_url=row['cover_image_url'],
            mal_url=row['mal_url'],
            updated_at=row['updated_at'],
            created_at=row['created_at']
        )
        chapters = json.loads(row['chapters'])
        genres = json.loads(row['genres'])
        authors = json.loads(row['authors'])
        results.append(
            MangaPageData(
                manga=manga,
                manga_num_views=row['views'] + 1,
                chapters=[MangaPageChapter(**dict(row)) for row in chapters],
                genres=[Genre(**dict(row)) for row in genres],
                authors=[MangaAuthor(**dict(row)) for row in authors],
                reading_status=None
            )
        )

    return Pagination[MangaPageData](
        total=total,
        limit=limit,
        offset=offset,
        results=results
    )


async def get_manga_carousel_list(limit: int, offset: int, conn: Connection) -> Pagination[MangaCarouselItem]:
    total: int = await db_count("manga_page_view", conn)

    rows = await conn.fetch(
        """
            SELECT
                *
            FROM
                manga_page_view
            ORDER BY
                RANDOM()
            LIMIT
                $1
            OFFSET
                $2
        """,
        limit,
        offset
    )

    results = []

    for row in rows:
        manga = Manga(
            id=row['id'],
            title=row['title'],
            descr=row['descr'],
            status=row['status'],
            color=row['color'],
            cover_image_url=row['cover_image_url'],
            mal_url=row['mal_url'],
            updated_at=row['updated_at'],
            created_at=row['created_at']
        )        
        genres = json.loads(row['genres'])
        authors = json.loads(row['authors'])
        results.append(
            MangaCarouselItem(
                manga=manga,
                genres=[Genre(**dict(row)) for row in genres],
                authors=[MangaAuthor(**dict(row)) for row in authors]                
            )
        )

    return Pagination[MangaCarouselItem](
        total=total,
        limit=limit,
        offset=offset,
        results=results
    )


async def refresh_manga_page_view(conn: Connection) -> None:
    await conn.execute("SELECT perform_refresh_manga_page_view()")