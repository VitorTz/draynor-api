from fastapi import FastAPI, Request, status
from fastapi.responses import FileResponse, Response
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from src.exceptions import DatabaseError
from src.routes import auth
from src.routes import user
from src.routes import chapter
from src.routes import library
from src.routes import collections
from src.routes import manga_request
from src.routes import bug_reports
from src.routes import manga
from src.routes import admin
from src.routes import admin_users
from src.routes import admin_genres
from src.routes import admin_manga_genres
from src.routes import admin_authors
from src.routes import admin_mangas
from src.routes import admin_manga_authors
from src.routes import admin_collections
from src.routes import admin_logs
from src.routes import admin_chapter_images
from src.routes import admin_chapters
from src.routes import admin_bug_reports
from src.routes import admin_manga_request
from src.routes import admin_manga_blacklist
from src.monitor import get_monitor, periodic_update
from src import db
from src import middleware
from src import globals
from src import util
from src.cloudflare import CloudflareR2Bucket
from src.models import log as log_model
from src.models import manga as manga_model
from src.constants import Constants
import time
import asyncio
import contextlib
import os



async def background_refresh_task():
    while True:
        try:
            pool = db.get_db_pool()
            conn = await pool.acquire()
            await manga_model.refresh_manga_page_view(conn)
            print("[INFO] manga_page_view updated.")
        except Exception as e:
            print(f"[ERROR] Erro ao atualizar manga_page_view: {e}")
        finally:
            await pool.release(conn)
        await asyncio.sleep(600)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[Starting {Constants.API_NAME}]")
    # [PostgreSql INIT]
    await db.db_init()

    # [System Monitor Task]
    task = asyncio.create_task(periodic_update())

    # [Database tasks]
    task_refresh_manga_page_vuew = asyncio.create_task(background_refresh_task())

    # [Cloudflare]
    app.state.r2 = await CloudflareR2Bucket.get_instance()

    print(f"[{Constants.API_NAME} STARTED]")

    yield

    # [SystemMonitor]
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    # [Database tasks]
    task_refresh_manga_page_vuew.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task_refresh_manga_page_vuew

    # [PostgreSql CLOSE]
    await db.db_close()

    # [Cloudflare]
    if hasattr(app.state.r2, "close"):
        await app.state.r2.close()

    print(f"[Shutting down {Constants.API_NAME}]")



app = FastAPI(    
    title=Constants.API_NAME, 
    description=Constants.API_DESCR,
    version=Constants.API_VERSION,
    lifespan=lifespan
)


app.mount("/static", StaticFiles(directory="static"), name="static")

if Constants.IS_PRODUCTION:
    origins = [
        "https://vitortz.github.io",
        "https://vitortz.github.io/draynor-client"
    ]
else:
    origins = [
        "http://localhost:5173"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return { "status": "ok" }


@app.get("/favicon.ico")
async def favicon():
    favicon_path = os.path.join("static", "favicon_io/favicon.ico")
    return FileResponse(favicon_path)


app.include_router(auth.router, prefix='/api/v1/auth', tags=['auth'])
app.include_router(user.router, prefix='/api/v1/user', tags=['user'])
app.include_router(manga.router, prefix='/api/v1/mangas', tags=['mangas'])
app.include_router(chapter.router, prefix='/api/v1/chapters', tags=['chapters'])
app.include_router(library.router, prefix='/api/v1/library', tags=["library"])
app.include_router(collections.router, prefix='/api/v1/collections', tags=["collections"])
app.include_router(manga_request.router, prefix='/api/v1/manga/requests', tags=["manga_requests"])
app.include_router(bug_reports.router, prefix='/api/v1/reports/bugs', tags=["bug_reports"])
app.include_router(admin.router, prefix='/api/v1/admin', tags=["admin_core"])
app.include_router(admin_users.router, prefix='/api/v1/admin/users', tags=["admin_users"])
app.include_router(admin_authors.router, prefix='/api/v1/admin/authors', tags=["admin_authors"])
app.include_router(admin_genres.router, prefix='/api/v1/admin/genres', tags=["admin_genres"])
app.include_router(admin_mangas.router, prefix='/api/v1/admin/mangas', tags=["admin_mangas"])
app.include_router(admin_manga_authors.router, prefix='/api/v1/admin/mangas/authors', tags=["admin_manga_authors"])
app.include_router(admin_manga_genres.router, prefix='/api/v1/admin/mangas/genres', tags=["admin_manga_genres"])
app.include_router(admin_chapters.router, prefix='/api/v1/admin/chapters', tags=["admin_chapters"])
app.include_router(admin_chapter_images.router, prefix='/api/v1/admin/chapters/images', tags=["admin_chapters_images"])
app.include_router(admin_collections.router, prefix='/api/v1/admin/collections', tags=["admin_collections"])
app.include_router(admin_manga_request.router, prefix='/api/v1/admin/manga/requests', tags=["admin_manga_request"])
app.include_router(admin_bug_reports.router, prefix='/api/v1/admin/reports/bugs', tags=["admin_bug_reports"])
app.include_router(admin_manga_blacklist.router, prefix='/api/v1/admin/blacklist/mangas', tags=["admin_manga_blacklist"])
app.include_router(admin_logs.router, prefix='/api/v1/admin/logs', tags=["admin_logs"])


app.add_middleware(GZipMiddleware, minimum_size=1000)


########################## MIDDLEWARES ##########################

@app.middleware("http")
async def http_middleware(request: Request, call_next):
    if Constants.IS_PRODUCTION:
        if request.method == "OPTIONS":
            origin = request.headers.get("origin")
            if origin in [
                "https://vitortz.github.io",
                "https://vitortz.github.io/draynor-client"
            ]:
                headers = {
                    "Access-Control-Allow-Origin": "https://vitortz.github.io",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": request.headers.get("access-control-request-headers", "*"),
                }
                return Response(status_code=200, headers=headers)
            return Response(status_code=403)
     
    if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
        response = await call_next(request)
        return response
    
    start_time = time.perf_counter()
    
    # Body size check
    content_length = request.headers.get("content-length")
    if content_length:
        if int(content_length) > Constants.MAX_BODY_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Request entity too large. Max allowed: {Constants.MAX_BODY_SIZE} bytes"
            )
    else:
        body = b""
        async for chunk in request.stream():
            body += chunk
            if len(body) > Constants.MAX_BODY_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"Request entity too large. Max allowed: {Constants.MAX_BODY_SIZE} bytes"
                )
        request._body = body
    
    # Rate limit check
    identifier = util.get_client_identifier(request)
    key = f"rate_limit:{identifier}"
    
    pipe = globals.globals_get_redis_client().pipeline()
    pipe.incr(key)
    pipe.expire(key, Constants.WINDOW)
    results = await pipe.execute()
    
    current = results[0]
    ttl = await globals.globals_get_redis_client().ttl(key)
    
    if current > Constants.MAX_REQUESTS:    
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Too many requests",
                "message": f"Rate limit exceeded. Try again in {ttl} seconds.",
                "retry_after": ttl,
                "limit": Constants.MAX_REQUESTS,
                "window": Constants.WINDOW
            },
            headers={
                "Retry-After": str(ttl),
                "X-RateLimit-Limit": str(Constants.MAX_REQUESTS),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(ttl)
            }
        )
    
    # Headers
    response: Response = await call_next(request)
        
    remaining = max(Constants.MAX_REQUESTS - current, 0)
    response.headers["X-RateLimit-Limit"] = str(Constants.MAX_REQUESTS)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(ttl)
        
    middleware.add_security_headers(request, response)
    response_time_ms = (time.perf_counter() - start_time) * 1000
    response.headers["X-Response-Time"] = f"{response_time_ms:.2f}ms"
    
    # System Monitor
    get_monitor().increment_request(response_time_ms)

    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return await log_model.log_and_build_response(
        request=request,
        exc=exc,
        error_level="WARN" if exc.status_code < 500 else "ERROR",
        status_code=exc.status_code,
        detail=exc.detail
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return await log_model.log_and_build_response(
        request=request,
        exc=exc,
        error_level="WARN",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "message": "Validation error",
            "errors": exc.errors()
        }
    )


@app.exception_handler(DatabaseError)
async def global_exception_handler(request: Request, exc: DatabaseError):
    return await log_model.log_and_build_response(
        request=request,
        exc=exc,
        error_level="ERROR",
        status_code=exc.code if exc.code else status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=exc.detail
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return await log_model.log_and_build_response(
        request=request,
        exc=exc,
        error_level="FATAL",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error"
    )
