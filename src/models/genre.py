from src.schemas.genre import GenreCreate, Genre, GenreDelete, MangaGenreCreate, MangaGenre, MangaGenreList
from src.schemas.general import Pagination, IntId
from asyncpg import Connection
from src.db import db_count
from src.exceptions import DatabaseError


async def get_genres(limit: int, offset: int, conn: Connection) -> Pagination[Genre]:
    total = await db_count("genres", conn)
    rows = await conn.fetch(
        """
            SELECT
                id,
                genre,
                created_at
            FROM
                genres
            ORDER BY
                genre ASC
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
        results=[Genre(**dict(row)) for row in rows]
    )



async def create_genre(genre: GenreCreate, conn: Connection) -> Genre:
    row = await conn.fetchrow(
        """
        INSERT INTO genres (
            genre
        )
        VALUES 
            (INITCAP(TRIM($1)))
        ON CONFLICT 
            (genre) 
        DO NOTHING
        RETURNING 
            id, 
            genre, 
            created_at;
        """,
        genre.genre,
    )
    
    if not row:
        row = await conn.fetchrow(
            """
                SELECT 
                    id, 
                    genre, 
                    created_at 
                FROM 
                    genres 
                WHERE 
                    genre = INITCAP(TRIM($1));
            """,
            genre.genre,
        )

    return Genre(**dict(row))


async def delete_genre(genre: IntId, conn: Connection) -> None:
    await conn.execute(
        """
            DELETE FROM
                genres
            WHERE
                id = $1
        """,
        genre.id
    )


async def create_manga_genre(manga_genre: MangaGenreCreate, conn: Connection) -> MangaGenre:
    r = await conn.fetchval("SELECT id FROM mangas WHERE id = $1", manga_genre.manga_id)
    if not r:
        raise DatabaseError(
            detail=f'manga with id {manga_genre.manga_id} not found',
            code=404
        )
    
    await conn.execute(
        """
            INSERT INTO manga_genres (
                genre_id,
                manga_id
            )
            VALUES
                ($1, $2)
            ON CONFLICT
                (genre_id, manga_id)
            DO NOTHING
        """,
        manga_genre.genre_id,
        manga_genre.manga_id
    )


async def get_manga_genres(manga: IntId, conn: Connection) -> MangaGenreList:
    rows = await conn.fetch(
        """
            SELECT
                genre.id,
                genre.genre,
                genre.created_at
            FROM
                genres
            JOIN
                manga_genres ON manga_genres.genre_id = genres.id
            WHERE
                manga_genres.manga_id = $1
            ORDER BY
                genres.genre ASC
        """,
        manga.id
    )
    return MangaGenreList(
        manga_id=manga.id, 
        genres=[Genre(**dict(row)) for row in rows]
    )


async def delete_manga_genre(manga_genre: MangaGenreCreate, conn: Connection) -> None:
    await conn.execute(
        """
            DELETE FROM
                manga_genres
            WHERE
                genre_id = $1
                AND manga_id = $2
        """,
        manga_genre.genre_id,
        manga_genre.manga_id
    )