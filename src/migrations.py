from asyncpg import Connection
from pathlib import Path
from datetime import datetime
from src import util
from src.cloudflare import CloudflareR2Bucket
from typing import Any
import uuid
import csv
import json


def read_json(path: Path):
    with open(path, "r") as file:
        return json.load(file)


def save_json(obj: Any, path: Path):
    with open(path, "w+") as file:
        json.dump(obj, file, indent=True)


async def manga_migrations(conn: Connection) -> None:
    mangas = read_json(Path("res/mangas.json"))
    params = []
    for manga in mangas:
        params.append((
            manga['manga_id'],
            manga['title'],
            manga['descr'],
            manga['cover_image_url'],
            manga['status'].title(),
            manga['color'],             
            manga['mal_url']
        ))
        
    await conn.executemany(
        """
            INSERT INTO mangas (
                id,
                title,
                descr,
                cover_image_url,
                status,
                color,
                mal_url
            )
            VALUES
                ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT
                (id)
            DO NOTHING
        """,
        params
    )
    
    
async def authors_migrations(conn: Connection) -> None:
    authors = read_json("res/authors.json")
    params = []
    for author in authors:
        params.append((
            author['author_id'],
            author['name']
        ))
        
    await conn.executemany(
        """
            INSERT INTO authors (
                id,
                name   
            )
            VALUES
                ($1, $2)
            ON CONFLICT
                (name)
            DO NOTHING
        """,
        params
    )
    
async def manga_authors_migrations(conn: Connection) -> None:
    authors = read_json("res/authors.json")
    manga_authors = read_json("res/manga_authors.json")
    
    authors_map = {}
    for author in authors:
        authors_map[author['author_id']] = author
        
    params = []
    # author_id, manga_id, role
    
    rows = await conn.fetch(
        """
            SELECT
                id,
                name
            FROM
                authors
        """
    )
    
    author_id_map = {
        row['name']: row['id'] for row in rows
    }
    
    for manga_author in manga_authors:
        author_name = authors_map[manga_author['author_id']]['name']
        role = authors_map[manga_author['author_id']]['role']
        author_id = author_id_map[author_name]
        params.append((
            author_id,
            manga_author['manga_id'],
            role
        ))
        
    await conn.executemany(
        """
            INSERT INTO manga_authors (
                author_id,
                manga_id,
                role  
            )
            VALUES
                ($1, $2, $3)
        """,
        params
    )
    

async def genres_migrations(conn: Connection) -> None:
    genres = read_json("res/genres.json")
    params = []
    for genre in genres:
        params.append((
            genre['genre_id'],
            genre['genre']
        ))
    
    await conn.executemany(
        """
            INSERT INTO genres (
                id,
                genre
            )
            VALUES
                ($1, $2)
        """,
        params
    )
    
    
async def manga_genres_migrations(conn: Connection) -> None:
    manga_genres = read_json("res/manga_genres.json")
    params = []
    for manga_genre in manga_genres:
        params.append((
            manga_genre['genre_id'],
            manga_genre['manga_id']
        ))
        
    await conn.executemany(
        """
        INSERT INTO manga_genres (genre_id, manga_id) VALUES ($1, $2)
        """,
        params
    )
    
    
async def chapter_images_migrations(conn: Connection) -> None:

    for i in range(8):
        path = f"res/images/chapter_images_p{i}_rows.csv"
        params = []
        
        with open(path, newline="", encoding="utf-8") as f:
            leitor = csv.DictReader(f)            

            for linha in leitor:
                params.append((
                    int(linha['chapter_id']),
                    int(linha['index']),
                    linha['image_url'],
                    int(linha['width']),
                    int(linha['height'])
                ))
                
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
                    DO NOTHING
                """,
                params
            )            
            
            
async def add_images(conn: Connection) -> None:
    bucket = await CloudflareR2Bucket.get_instance()
    images = read_json("res/image.json")
    for image in images:
        manga_id = image['id']
        manga_title = image['title']
        image_url = image['cover_image_url']
        if image_url:
            try:
                path = Path("tmp/image.webp")
                util.download_resize_to_webp(image_url, path)
                manga_name = util.normalize_to_url(image['title'])
                new_image_url: str = await bucket.upload_file(
                    key=f"mangas/cover/{manga_name}-{uuid.uuid4()}.webp",
                    file_path=path,
                    content_type="image/webp"
                )
                await conn.execute(
                    """
                        UPDATE
                            mangas
                        SET
                            cover_image_url = $1
                        WHERE
                            id = $2
                    """,
                    new_image_url,
                    manga_id
                )
                print(f"[NEW {manga_title} -> {new_image_url}]")
                image['cover_image_url'] = ''
                save_json(images, "res/image.json")
            except Exception as e:
                print(e)
                print(image)
                return