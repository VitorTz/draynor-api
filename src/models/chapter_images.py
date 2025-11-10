from asyncpg import Connection
from src.schemas.chapter import ChapterImage, ChapterImageList, Chapter, ChapterImageListCreate, ChapterImageCreate, ChapterImageDelete
from src.schemas.general import IntId, Pagination
from src.schemas.manga import Manga
from src.exceptions import DatabaseError
from src.db import db_count


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
    row = await conn.fetchrow(
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
        chapter_id
    )

    if not row:
        raise DatabaseError(detail=f"chapter with id {chapter_id} not found", code=404)
    
    chapter_model = Chapter(**dict(row))

    row = await conn.fetchrow(
        """
            SELECT
                id,
                title,
                descr,
                color,
                cover_image_url,
                status,
                updated_at,
                created_at,
                mal_url
            FROM
                mangas
            WHERE
                id = $1     
        """,
        chapter_model.manga_id
    )

    if not row:
        raise DatabaseError(detail=f"manga with id {chapter_model.manga_id} not found", code=404)

    manga_model = Manga(**dict(row))

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
            WHERE
                chapter_id = $1
            ORDER BY
                image_index ASC
        """,
        chapter_id
    )

    images = [ChapterImage(**dict(row)) for row in rows]

    return ChapterImageList(
        manga=manga_model,
        chapter=chapter_model,
        num_images=len(images),
        images=images
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