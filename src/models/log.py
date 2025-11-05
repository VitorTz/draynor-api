from src.schemas.log import (
    Log, 
    DeletedLogs, 
    LogDailyStat, 
    LogErrorEndpoint, 
    LogHourlyStat, 
    LogLevelStat, 
    LogMethodStat, 
    LogStats, 
    LogStatusStat
)
from fastapi import Request
from fastapi.responses import JSONResponse
from src.schemas.general import Pagination
from src.monitor import get_monitor
from src.db import get_db_pool, db_count
from asyncpg import Connection
from datetime import datetime
from typing import Literal, Optional
import json
import traceback


async def add_log_error(
    error_level: str,
    message: str,
    path: str,
    method: str,
    status_code: int,
    stacktrace: str,
    metadata: dict,
    conn: Connection = None
):
    try:
        if conn is not None:
            await conn.execute(
                """
                INSERT INTO logs (
                    level, 
                    message, 
                    path, 
                    method, 
                    status_code, 
                    stacktrace,
                    metadata
                )
                VALUES 
                    ($1, $2, $3, $4, $5, $6, $7)
                """,
                error_level,
                message,
                path,
                method,
                status_code,
                stacktrace,
                json.dumps(metadata)
            )
        else:
            print(
                f"[{error_level}] {method} {path} - {status_code}\n",
                f"Message: {message}\n",
                f"Stacktrace: {stacktrace}"
            )
    except Exception as e:
        print(
            f"Failed to log to database: {e}\n",
            f"Original error: [{error_level}] {method} {path} - {status_code}\n",
            f"{message}\n{stacktrace}"
        )


async def log_error(
    request: Request,
    exc: Exception,
    error_level: Literal['DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL'],
    status_code: int,
    detail: dict | str
):
    get_monitor().increment_error()
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        
    metadata = {
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "referer": request.headers.get("referer"),
        "content_type": request.headers.get("content-type"),            
        "query_params": dict(request.query_params) if request.query_params else None,
        "path_params": dict(request.path_params) if request.path_params else None,
        "request_id": request.headers.get("x-request-id"),
        "exception_type": type(exc).__name__,
        "exception_module": type(exc).__module__,
        "timestamp_ms": int(datetime.now().timestamp() * 1000),
        "host": request.url.hostname,
        "scheme": request.url.scheme,
        "server": request.headers.get("host"),
        "auth_header_present": "authorization" in request.headers,
        "response_detail": str(detail) if isinstance(detail, str) else detail,
        "correlation_id": request.state.correlation_id if hasattr(request.state, 'correlation_id') else None,
    }
        
    metadata = {k: v for k, v in metadata.items() if v is not None}
    
    conn = None
    try:
        pool = get_db_pool()
        if pool is not None:
            conn = await pool.acquire()
            await add_log_error(
                error_level=error_level,
                message=str(exc),
                path=str(request.url.path),
                method=request.method,
                status_code=status_code,
                stacktrace=tb,
                metadata=metadata,
                conn=conn
            )
    except Exception as e:
        print(f"Failed to acquire DB connection for logging: {e}")
        await add_log_error(
            error_level=error_level,
            message=str(exc),
            path=str(request.url.path),
            method=request.method,
            status_code=status_code,
            stacktrace=tb,
            metadata=metadata,
            conn=None
        )
    finally:
        if conn is not None:
            try:
                await pool.release(conn)
            except Exception as e:
                print(f"Failed to release DB connection: {e}")


async def log_and_build_response(
    request: Request,
    exc: Exception,
    error_level: Literal['DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL'],
    status_code: int,
    detail: dict | str
) -> JSONResponse:
    await log_error(request, exc, error_level, status_code, detail)
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": str(detail),
            "path": str(request.url.path),
            "status_code": status_code,
            "timestamp": str(datetime.now())
        }
    )


async def get_logs(
    limit: int,
    offset: int,
    conn: Connection
) -> Pagination[Log]:
    total: int = await db_count('logs', conn)
    rows = await conn.fetch(
        f"""
            SELECT 
                id,
                level,
                message,
                path,
                method,
                status_code,
                stacktrace,
                metadata,
                created_at
            FROM 
                logs
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
        results=[Log(**dict(i)) for i in rows]
    )


async def delete_logs(interval_minutes: Optional[int], method: Optional[Literal['GET', 'PUT', 'POST', 'DELETE']], conn: Connection) -> DeletedLogs:
    t1: int = await db_count('logs', conn)

    base_query = "DELETE FROM logs WHERE TRUE"
    params = []

    if interval_minutes is not None:
        base_query += " AND created_at < NOW() - ($1 * INTERVAL '1 minute')"
        params.append(interval_minutes)

    if method is not None:
        param_index = len(params) + 1
        base_query += f" AND method = ${param_index}"
        params.append(method)

    await conn.execute(base_query, *params)

    t2: int = await db_count('logs', conn)

    return DeletedLogs(total=t1 - t2)


async def get_log_stats(conn: Connection) -> LogStats:
    # Estatísticas por nível
    level_stats = await conn.fetch("""
        SELECT 
            level, 
            COUNT(*) as count
        FROM 
            logs
        GROUP BY 
            level
        ORDER BY 
            count DESC
    """)
    
    # Estatísticas por status code
    status_stats = await conn.fetch("""
        SELECT 
            CASE 
                WHEN status_code >= 200 AND status_code < 300 THEN '2xx'
                WHEN status_code >= 300 AND status_code < 400 THEN '3xx'
                WHEN status_code >= 400 AND status_code < 500 THEN '4xx'
                WHEN status_code >= 500 AND status_code < 600 THEN '5xx'
                ELSE 'Other'
            END as status_group,
            COUNT(*) as count
        FROM logs
        WHERE status_code IS NOT NULL
        GROUP BY status_group
        ORDER BY status_group
    """)
    
    # Estatísticas por método HTTP
    method_stats = await conn.fetch("""
        SELECT method, COUNT(*) as count
        FROM logs
        WHERE method IS NOT NULL
        GROUP BY method
        ORDER BY count DESC
    """)
    
    # Logs por dia (últimos 7 dias)
    daily_stats = await conn.fetch("""
        SELECT 
            created_at AS date,
            COUNT(*) AS count
        FROM logs
        WHERE created_at >= NOW() - INTERVAL '7 days'
        GROUP BY date
        ORDER BY date DESC
    """)
    
    # Logs por hora (últimas 24 horas)
    hourly_stats = await conn.fetch("""
        SELECT 
            created_at AS hour,
            COUNT(*) AS count
        FROM 
            logs
        WHERE created_at >= NOW() - INTERVAL '24 hours'
        GROUP BY hour
        ORDER BY hour DESC
    """)
    
    # Top 10 endpoints com mais erros
    error_endpoints = await conn.fetch(
        """
            SELECT 
                path,
                COUNT(*) as count
            FROM logs
            WHERE level = 'ERROR'
            GROUP BY path
            ORDER BY count DESC
            LIMIT 10
        """
    )

    return LogStats(
        by_level=[LogLevelStat(**dict(row)) for row in level_stats],
        by_status=[LogStatusStat(**dict(row)) for row in status_stats],
        by_method=[LogMethodStat(**dict(row)) for row in method_stats],
        by_day=[LogDailyStat(**dict(row)) for row in daily_stats],
        by_hour=[LogHourlyStat(**dict(row)) for row in hourly_stats],
        error_endpoints=[LogErrorEndpoint(**dict(row)) for row in error_endpoints]
    )
