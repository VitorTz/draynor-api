from asyncpg import Connection
from typing import Optional, Literal
from src.schemas.general import Pagination, IntId
from src.schemas.chapter import Chapter, ChapterCreate, ChapterUpdate, MangaChapters
from src.schemas.manga import Manga
from src.db import db_count
from src.exceptions import DatabaseError


async def get_chapters(
    limit: int,
    offset: int, 
    conn: Connection,
    manga_id: Optional[int] = None
) -> Pagination[Chapter]:
    if manga_id:
        total: int = await conn.fetchval("SELECT COUNT(*) FROM chapters WHERE manga_id = $1", manga_id)
        rows = await conn.fetch(
            """
                SELECT
                    id,
                    manga_id,
                    chapter_index,
                    chapter_name,
                    created_at
                FROM
                    chapters
                WHERE
                    manga_id = $1
                ORDER BY
                    chapter_index ASC
                LIMIT
                    $2
                OFFSET
                    $3           
            """,
            manga_id,
            limit,
            offset
        )
    else:
        total: int = await db_count("chapters", conn)
        rows = await conn.fetch(
            """
                SELECT
                    id,
                    manga_id,
                    chapter_index,
                    chapter_name,
                    created_at
                FROM
                    chapters
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
        results=[Chapter(**dict(row)) for row in rows]
    )


async def get_manga_chapters(
    manga_id: int,
    limit: Optional[int],
    order: Literal['ASC', 'DESC'],
    conn: Connection
) -> MangaChapters:

    manga_row = await conn.fetchrow(
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
                id = $1
        """,
        manga_id
    )

    if not manga_row:
        raise DatabaseError(f"manga with id {manga_id} not found", code=404)

    manga = Manga(**dict(manga_row))

    # Validate order to prevent SQL injection
    if order not in ("ASC", "DESC"):
        raise DatabaseError("Invalid order parameter", code=400)

    order_sql = "ASC" if order == "ASC" else "DESC"

    base_query = f"""
        SELECT
            id,
            manga_id,
            chapter_index,
            chapter_name,
            created_at
        FROM
            chapters
        WHERE
            manga_id = $1
        ORDER BY
            chapter_index {order_sql}
    """

    if limit:
        base_query += " LIMIT $2"
        rows = await conn.fetch(base_query, manga.id, limit)
    else:
        rows = await conn.fetch(base_query, manga.id)

    return MangaChapters(
        manga=manga,
        chapters=[Chapter(**dict(row)) for row in rows]
    )

async def create_chapter(chapter: ChapterCreate, conn: Connection) -> Chapter:
    await conn.execute(
        """
            INSERT INTO chapters (
                id,
                manga_id,
                chapter_index,
                chapter_name
            )
            VALUES
                ($1, $2, $3, $4)
            ON CONFLICT
                (manga_id, chapter_index)
            DO NOTHING
        """,
        chapter.chapter_id,
        chapter.manga_id,
        chapter.chapter_index,
        chapter.chapter_name
    )

    r = await conn.fetchrow(
        """
            SELECT
                id,
                manga_id,
                chapter_index,
                chapter_name,
                created_at
            FROM
                chapters
            WHERE
                manga_id = $1
                AND chapter_index = $2
        """,
        chapter.manga_id,
        chapter.chapter_index
    )

    return Chapter(**dict(r))



async def update_chapter(chapter: ChapterUpdate, conn: Connection) -> Chapter:
    old_chapter = await conn.fetchrow(
        """
            SELECT 
                id, 
                manga_id,
                chapter_index,
                chapter_name,
                created_at
            FROM 
                chapters 
            WHERE 
                id = $1
        """, 
        chapter.id
    )

    if not old_chapter:
        raise DatabaseError(detail=f"chapter with id {chapter.id} not dound", code=404)

    old_chapter: dict = dict(old_chapter)

    if not chapter.chapter_index:
        chapter.chapter_index = old_chapter['chapter_index']

    if not chapter.chapter_name:
        chapter.chapter_name = old_chapter['chapter_name']

    new_chapter = old_chapter
    new_chapter['chapter_index'] = chapter.chapter_index
    new_chapter['chapter_name'] = chapter.chapter_name
    

    await conn.execute(
        """
            UPDATE 
                chapters
            SET
                chapter_index = $1
                AND chapter_name = $2
            WHERE
                id = $3
        """,
        chapter.chapter_index,
        chapter.chapter_name,
        chapter.id
    )
    
    return Chapter(**new_chapter)


async def delete_chapter(chapter: IntId, conn: Connection) -> None:
    await conn.execute(
        "DELETE FROM chapters WHERE id = $1",
        chapter.id
    )


async def delete_all_chapters(conn: Connection) -> None:
    await conn.execute("DELETE FROM chapters;")