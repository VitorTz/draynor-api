from asyncpg import Connection
from src.schemas.bug_report import BugReport, BugReportCreate, BugReportLiteral
from src.schemas.general import Pagination, IntId
from src.db import db_count
from typing import Optional


async def get_bug_reports(
    limit: int,
    offset: int,
    bug_type: Optional[BugReportLiteral],
    conn: Connection
) -> Pagination[BugReport]:
    if bug_type:
        total: int = await conn.fetchval(
            """
                SELECT
                    COUNT(*)
                FROM
                    bug_reports
                WHERE
                    bug_type = $1
            """,
            bug_type
        )
        rows = await conn.fetch(
            """
                SELECT
                    id,
                    title,
                    descr,
                    bug_type,
                    created_at
                FROM
                    bug_reposts
                WHERE
                    bug_type = $1
                ORDER BY
                    created_at DESC
                LIMIT
                    $2
                OFFSET
                    $3
            """,
            bug_type,
            limit,
            offset
        )
    else:
        total: int = await db_count("bug_reports", conn)
        rows = await conn.fetch(
            """
                SELECT
                    id,
                    title,
                    descr,
                    bug_type,
                    created_at
                FROM
                    bug_reposts
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
        results=[BugReport(**dict(row)) for row in rows]
    )


async def create_bug_report(bug_report: BugReportCreate, conn: Connection) -> BugReport:
    row = await conn.execute(
        """
            INSERT INTO bug_reports (
                title,
                descr,
                bug_type
            )
            VALUES
                ($1, $2, $3)
            RETURNING
                id,
                title,
                descr,
                bug_type,
                created_at
        """,
        bug_report.title,
        bug_report.descr,
        bug_report.bug_type
    )
    return BugReport(**dict(row))


async def delete_bug_report(bug_report: IntId, conn: Connection):
    await conn.execute(
        """
            DELETE FROM
                bug_reports
            WHERE
                id = $1
        """,
        bug_report.id
    )