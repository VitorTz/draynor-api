from asyncpg import Connection
from src.schemas.general import IntId


async def add_view_to_manga(manga: IntId, conn: Connection):
    await conn.execute(
        """
            UPDATE  
                manga_metrics
            SET
                total_reads = total_reads + 1
            WHERE
                manga_id = $1
        """,
        manga.id
    )