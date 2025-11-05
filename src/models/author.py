from src.schemas.author import Author, AuthorCreate, AuthorUpdate, MangaAuthorList, AuthorWithRole, MangaAuthorDelete, MangaAuthorCreate, MangaAuthor
from asyncpg import Connection
from src.schemas.general import Pagination, IntId
from src.exceptions import DatabaseError
from src.db import db_count


async def get_authors(limit: int, offset: int, conn: Connection) -> Pagination[Author]:
    total = await db_count("authors", conn)
    rows = await conn.fetch(
        """
            SELECT
                id,
                name,
                created_at     
            FROM
                authors
            ORDER BY
                name ASC
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
        results=[Author(**dict(row)) for row in rows]
    )


async def get_manga_authors_pagination(limit: int, offset: int, conn: Connection) -> Pagination[MangaAuthor]:
    total = await db_count("manga_authors", conn)
    rows = await conn.fetch(
        """
            SELECT
                author_id,
                manga_id,
                role,
                created_at
            FROM
                manga_authors
            ORDER BY
                author_id ASC
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
        results=[MangaAuthor(**dict(row)) for row in rows]
    )

async def get_manga_authors(manga: IntId, conn: Connection) -> MangaAuthorList:
    rows = await conn.fetch(
        """
        SELECT
            a.id,
            a.name,
            a.created_at,
            ma.role
        FROM
            authors a
        JOIN
            manga_authors ma ON ma.author_id = a.id
        WHERE
            ma.manga_id = $1
        ORDER BY
            ma.role ASC,
            a.name ASC;
        """,
        manga.id,
    )

    return MangaAuthorList(
        manga_id=manga.id,
        authors=[AuthorWithRole(**dict(row)) for row in rows]
    )


async def create_author(author: AuthorCreate, conn: Connection) -> Author:
    r = await conn.fetchrow(
        """
            INSERT INTO authors (
                name
            )
            VALUES
                (INITCAP(TRIM($1)))
            ON CONFLICT
                (name)
            DO NOTHING
            RETURNING
                id,
                name,
                created_at
        """,
        author.name
    )
    
    if not r:
        r = await conn.fetchrow(
            """
                SELECT
                    id,
                    name,
                    created_at
                FROM
                    authors
                WHERE
                    name = INITCAP(TRIM($1))
            """,
            author.name
        )

    return Author(**dict(r))


async def update_author(author: AuthorUpdate, conn: Connection) -> Author:
    r = await conn.fetchrow(
        """
        UPDATE 
            authors
        SET 
            name = $1
        WHERE 
            id = $2
        RETURNING 
            id, 
            name, 
            created_at;
        """,
        author.name,
        author.id
    )

    if not r:
        raise DatabaseError(
            detail=f"author with id {author.id} not found",
            code="404"
        )

    return Author(**dict(r))
    


async def delete_author(author: IntId, conn: Connection) -> None:
    await conn.execute(
        """
            DELETE FROM
                authors
            WHERE
                id = $1
        """,
        author.id
    )


async def create_manga_author(author: MangaAuthorCreate, conn: Connection) -> None:
    await conn.execute(
        """
            INSERT INTO manga_authors (
                author_id,
                manga_id,
                role
            )
            VALUES
                ($1, $2, TRIM($3))
            ON CONFLICT
                (author_id, manga_id, role)
            DO NOTHING
        """,
        author.author_id,
        author.manga_id,
        author.role
    )


async def delete_manga_author(author: MangaAuthorDelete, conn: Connection) -> None:
    await conn.execute(
        """
            DELETE FROM
                manga_authors
            WHERE
                author_id = $1
                AND manga_id = $2
                AND role = $3
        """,
        author.author_id,
        author.manga_id,
        author.role
    )