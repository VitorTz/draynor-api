from src.schemas.comments import Comment, CommentCreate, CommentReply
from src.schemas.general import Pagination
from src.schemas.user import User
from asyncpg import Connection


async def get_comment_thread(comment_id: int, conn: Connection):
    rows = await conn.fetch(
        """
            SELECT 
                *
            FROM 
                manga_comments
            WHERE path <@ (
                SELECT path FROM manga_comments WHERE id = $1
            )
            ORDER BY 
                path;
        """
    )

    return [dict(row) for row in rows]


async def create_comment(comment: CommentCreate, user: User, conn: Connection) -> Comment:
    row = await conn.fetchrow(
        """
            INSERT INTO manga_comments (
                manga_id,
                user_id,
                comment
            )
            VALUES
                ($1, $2, $3)
            RETURNING
                id,
                manga_id,
                user_id,
                comment,
                parent_id,
                path,
                created_at
        """,
        comment.manga_id,
        user.id, 
        comment.comment    
    )
        
    return Comment(**dict(row), total_replies=0)


async def reply_comment(comment: CommentReply, user: User, conn: Connection) -> Comment:
    row = await conn.fetchrow(
        """
            INSERT INTO manga_comments (
                manga_id,
                parent_id,
                user_id,
                comment
            )
            VALUES
                ($1, $2, $3, $4)
            RETURNING
                id,
                manga_id,
                user_id,
                comment,
                parent_id,
                path,
                created_at
        """,
        comment.manga_id,
        comment.parent_id,
        user.id,
        comment.comment
    )

    return Comment(**dict(row), total_replies=0)



async def delete_comment(comment_id: int, user: User, conn: Connection) -> None:
    await conn.execute(
        "DELETE FROM manga_comments WHERE id = $1 AND user_id = $2", 
        comment_id, 
        user.id
    )


async def get_manga_root_comments(manga_id: int, limit: int, offset: int, conn: Connection) -> Pagination[Comment]:
    total: int = await conn.fetchval(
        "SELECT COUNT(*) FROM manga_comments WHERE manga_id = $1 AND parent_id IS NULL",
        manga_id
    )

    rows = await conn.fetch(
        """
            SELECT 
                mc.*,
                (
                    SELECT COUNT(*) - 1
                    FROM manga_comments AS sub
                    WHERE sub.path <@ (
                        SELECT path FROM manga_comments WHERE id = $1
                    )
                ) AS total_replies
            FROM 
                manga_comments mc
            WHERE 
                mc.manga_id = $1 AND
                mc.parent_id IS NULL
            ORDER BY 
                mc.path;
        """,
        manga_id
    )

    return Pagination[Comment](
        total=total,
        limit=limit,
        offset=offset,
        results=[Comment(**dict(row)) for row in rows]
    )