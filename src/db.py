from asyncpg import create_pool, Pool, Connection
from dotenv import load_dotenv
from pathlib import Path
from src import migrations
from src import util
import psycopg
import os


load_dotenv()


db_pool: Pool = None


async def db_init() -> None:
    global db_pool
    database_url = os.getenv("DATABASE_URL")
    db_pool = await create_pool(database_url, min_size=5, max_size=20, statement_cache_size=0)
    async with db_pool.acquire() as conn:
        await util.execute_sql_file(Path("db/schema.sql"), conn)        
        await migrations.add_images(conn)


def db_instance() -> psycopg.Connection:
    database_url = os.getenv("DATABASE_URL")
    conn = psycopg.connect(database_url)
    return conn


def get_db_pool() -> Pool:
    global db_pool
    return db_pool


async def db_close() -> None:
    await db_pool.close()


async def get_db():
    async with db_pool.acquire() as conn:
        yield conn


async def db_count(table: str, conn: Connection) -> int:
    return await conn.fetchval(f"SELECT COUNT(*) AS total FROM {table};")


async def db_version(conn: Connection) -> str:
    r = await conn.fetchrow("SELECT version()")    
    return r['version']