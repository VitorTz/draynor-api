from src.schemas.collection import (
    Collection, 
    CollectionCreate, 
    CollectionMangaCreate, 
    CollectionMangaDelete, 
    CollectionUpdate
)
from asyncpg import Connection
from src.schemas.general import Pagination, IntId
from src.schemas.manga import Manga
from src.exceptions import DatabaseError
from src.util import coalesce
from src.db import db_count


async def get_collections(
    limit: int,
    offset: int,
    conn: Connection
) -> Pagination[Collection]:
    total: int = await db_count("collections", conn)    
    rows = await conn.fetch(
        """
            SELECT
                id,
                title,
                descr,
                created_at
            FROM
                collections
            ORDER BY
                title ASC
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
        results=[Collection(**dict(row)) for row in rows]
    )


async def create_collection(
    colletion: CollectionCreate,
    conn: Connection
) -> Collection:
    row = await conn.fetchrow(
        """
            INSERT INTO collections (
                title,
                descr
            )
            VALUES
                (TRIM($1), TRIM($2))
            ON CONFLICT
                (title)
            DO UPDATE SET
                descr = EXCLUDED.descr
            RETURNING
                id,
                title,
                descr,
                created_at
        """,
        colletion.title,
        colletion.descr
    )

    return Collection(**dict(row))


async def update_collection(
    collection: CollectionUpdate,
    conn: Connection
) -> Collection:
    updated_collection = await conn.fetchrow(
        """
            SELECT
                id,
                title,
                descr,
                created_at
            FROM
                collections
            WHERE
                id = $1
        """,
        collection.id
    )
    if not updated_collection:
        raise DatabaseError(f"collection with id {collection.id} not found", code=404)
    
    updated_collection = Collection(**dict(updated_collection))

    updated_collection.title = coalesce(collection.title, updated_collection.title)
    updated_collection.descr = coalesce(collection.descr, updated_collection.descr)

    await conn.execute(
        """
            UPDATE
                collections
            SET
                title = $1,
                descr = $2
            WHERE
                id = $3
        """,
            updated_collection.title,
            updated_collection.descr,
            updated_collection.id
    )

    return updated_collection


async def delete_collection(collection: IntId, conn: Connection):
    await conn.execute(
        "DELETE FROM collections WHERE id = $1", 
        collection.id
    )


async def get_mangas_from_collection(
    collection: IntId, 
    limit: int, 
    offset: int, 
    conn: Connection
) -> Pagination[Manga]:
    total: int = await conn.fetchval(
        """
            SELECT
                COUNT(*)
            FROM
                collections_mangas
            WHERE
                collections_mangas.collection_id = $1
                AND collections_mangas.manga_id NOT IN (
                    SELECT manga_id FROM manga_blacklist
                )
        """,
        collection.id
    )

    rows = await conn.fetch(
        """
            SELECT
                m.id,
                m.title,
                m.descr,
                m.cover_image_url,
                m.status,
                m.color,
                m.created_at,
                m.updated_at,
                m.mal_url
            FROM
                collections_mangas cm
            JOIN
                mangas m ON cm.manga_id = m.id
            WHERE
                cm.collection_id = $1
                AND m.id NOT IN (
                    SELECT manga_id FROM manga_blacklist
                )
            ORDER BY
                m.title ASC
            LIMIT
                $2
            OFFSET
                $3
        """,
        collection.id,
        limit,
        offset
    )

    return Pagination(
        total=total,
        limit=limit,
        offset=offset,
        results=[Manga(**dict(row)) for row in rows]
    )


async def add_manga_to_collection(collection_manga: CollectionMangaCreate, conn: Connection):
    await conn.execute(
        """
            INSERT INTO collections_mangas (
                collection_id,
                manga_id
            )
            VALUES
                ($1, $2)
            ON CONFLICT
                (collection_id, manga_id)
            DO NOTHING
        """,
        collection_manga.collection_id,
        collection_manga.manga_id
    )


async def remove_manga_from_collection(collection_manga: CollectionMangaDelete, conn: Connection):
    await conn.execute(
        """ 
            DELETE FROM
                collections_mangas
            WHERE
                collection_id = $1
                AND manga_id = $2
        """,
        collection_manga.collection_id,
        collection_manga.manga_id
    )