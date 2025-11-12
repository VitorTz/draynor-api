from asyncpg import Connection
from src.schemas.chapter import ChapterImage, ChapterImageList, Chapter, ChapterImageListCreate, ChapterImageCreate, ChapterImageDelete
from src.schemas.general import IntId, Pagination
from src.schemas.manga import Manga
from src.exceptions import DatabaseError
from src.db import db_count
import asyncio


async def get_all_chapter_images(limit: int, offset: int, conn: Connection) -> Pagination[ChapterImage]:
    total: int = await db_count("chapter_images", conn)
    rows = await conn.fetch(
        """
            SELECT
                chapter_id,
                image_index,
                image_url,
                width,
                height,
                created_at
            FROM
                chapter_images
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
        results=[ChapterImage(**dict(row)) for row in rows]
    )


async def get_chapter_images(chapter_id: int, conn: Connection) -> ChapterImageList:
    # Busca capítulo e manga juntos via JOIN
    row = await conn.fetchrow(
        """
        SELECT 
            c.id AS chapter_id,
            c.manga_id,
            c.chapter_index,
            c.chapter_name,
            c.created_at AS chapter_created_at,
            m.id AS manga_id,
            m.title,
            m.descr,
            m.color,
            m.cover_image_url,
            m.status,
            m.updated_at,
            m.created_at AS manga_created_at,
            m.mal_url
        FROM chapters c
        JOIN mangas m ON m.id = c.manga_id
        WHERE c.id = $1
        """,
        chapter_id
    )

    if not row:
        raise DatabaseError(detail=f"chapter with id {chapter_id} not found", code=404)

    chapter_model = Chapter(
        id=row["chapter_id"],
        manga_id=row["manga_id"],
        chapter_index=row["chapter_index"],
        chapter_name=row["chapter_name"],
        created_at=row["chapter_created_at"],
    )

    manga_model = Manga(
        id=row["manga_id"],
        title=row["title"],
        descr=row["descr"],
        color=row["color"],
        cover_image_url=row["cover_image_url"],
        status=row["status"],
        updated_at=row["updated_at"],
        created_at=row["manga_created_at"],
        mal_url=row["mal_url"],
    )

    # Busca imagens
    rows = await conn.fetch(
        """
        SELECT
            chapter_id,
            image_index,
            image_url,
            width,
            height,
            created_at
        FROM chapter_images
        WHERE chapter_id = $1
        ORDER BY image_index
        """,
        chapter_id
    )

    images = [ChapterImage(**dict(r)) for r in rows]
    
    await conn.execute(
        """
        UPDATE manga_metrics
        SET total_reads = total_reads + 1
        WHERE manga_id = $1
        """,
        manga_model.id
    )    

    return ChapterImageList(
        manga=manga_model,
        chapter=chapter_model,
        num_images=len(images),
        images=images,
    )


async def create_chapter_image(chapter_image: ChapterImageCreate, conn: Connection) -> None:
    await conn.execute(
        """
            INSERT INTO chapter_images (
                chapter_id,
                image_index,
                image_url,
                width,
                height
            )
            VALUES
                ($1, $2, $3, $4, $5)
            ON CONFLICT
                (chapter_id, image_index)
            DO UPDATE SET
                image_url = EXCLUDED.image_url,
                width = EXCLUDED.width,
                height = EXCLUDED.height
        """,
        chapter_image.chapter_id,
        chapter_image.image_index,
        chapter_image.image_url,
        chapter_image.width,
        chapter_image.height
    )


async def create_chapter_images(chapter_images: ChapterImageListCreate, conn: Connection) -> None:
    args = [
        (chapter_images.chapter_id, image.image_index, image.image_url, image.width, image.height)
        for image in chapter_images.images
    ]
    await conn.executemany(
        """
            INSERT INTO chapter_images (
                chapter_id,
                image_index,
                image_url,
                width,
                height
            )
            VALUES
                ($1, $2, $3, $4, $5)
            ON CONFLICT
                (chapter_id, image_index)
            DO UPDATE SET
                image_url = EXCLUDED.image_url,
                width = EXCLUDED.width,
                height = EXCLUDED.height
        """,
        args
    )


async def delete_chapter_images(chapter: IntId, conn: Connection):
    await conn.execute("DELETE FROM chapter_images WHERE chapter_id = $1", chapter.id)


async def delete_chapter_image(chapter_image: ChapterImageDelete, conn: Connection):
    await conn.execute(
        "DELETE FROM chapter_images WHERE chapter_id = $1 AND image_index = $2", 
        chapter_image.chapter_id, 
        chapter_image.image_index
    )