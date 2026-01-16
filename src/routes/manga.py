from src.schemas.manga import Manga
from src.schemas.general import Pagination
from src.schemas.manga_page import MangaPageData, MangaCarouselItem
from src.schemas.user import User
from src.schemas.genre import Genre
from src.models import genre as genre_model
from fastapi import APIRouter, Query, Depends, status
from src.models import manga as manga_model
from src.db import get_db
from asyncpg import Connection
from src.security import get_user_from_token_if_exists
from typing import Optional, Literal
from src.cache import SizeBasedAPICache


router = APIRouter()
cache = SizeBasedAPICache()


@router.get("/search")
async def get_mangas_by_title(
    q: str = Query(...),
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
) -> Pagination[Manga]:    
    return await cache.get_or_compute(
        key=f"search:{q}:{limit}:{offset}",        
        fetch_func=lambda: manga_model.get_mangas(limit, offset, conn, q),
        response_model=Pagination[Manga]
    )


@router.get("/search/complete")
async def search_mangas_complete(
    title: Optional[str] = Query(default=None),
    genre_id: Optional[int] = Query(default=None),
    order: Literal['ASC', 'DESC'] = Query(default='ASC'),
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
) -> Pagination[Manga]:
    return await cache.get_or_compute(
        key=f"search:{title}:{genre_id}:{order}:{limit}:{offset}",
        fetch_func=lambda: manga_model.get_mangas_complete(title, genre_id, order, limit, offset, conn),
        response_model=Pagination[Manga]
    )    


@router.get("/popular", response_model=Pagination[Manga])
async def get_most_popular_mangas(
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
) -> Pagination[Manga]:
    
    return await cache.get_or_compute(
        key=f"popular:{limit}:{offset}",
        fetch_func=lambda: manga_model.get_popular_mangas(limit, offset, conn),
        response_model=Pagination[Manga]
    )


@router.get("/page")
async def get_manga_page_data(
    manga_id: int = Query(...), 
    user: Optional[User] = Depends(get_user_from_token_if_exists),
    conn: Connection = Depends(get_db)
) -> MangaPageData:    
    return await manga_model.get_manga_page_data(manga_id, user, conn)


@router.get("/page/list")
async def get_mangas_page_data(
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
) -> Pagination[MangaCarouselItem]:
    
    return await cache.get_or_compute(
        key=f"page_list:{limit}:{offset}",
        fetch_func=lambda: manga_model.get_manga_carousel_list(limit, offset, conn),
        response_model=Pagination[MangaCarouselItem],
        ttl=300
    )
    

@router.get("/latest", response_model=Pagination[Manga])
async def get_latest_mangas(
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
) -> Pagination[Manga]: 
    
    return await cache.get_or_compute(
        key=f"latest:{limit}:{offset}",
        fetch_func=lambda: manga_model.get_latest_mangas(limit, offset, conn),
        response_model=Pagination[Manga],
        ttl=300
    )
    

@router.get("/random", status_code=status.HTTP_200_OK, response_model=Pagination[Manga])
async def get_random_mangas(
    limit: int = Query(default=64, ge=0, le=64),
    conn: Connection = Depends(get_db)
) -> Pagination[Manga]:
    return await manga_model.get_random_mangas(limit, conn)


@router.get("/genre", response_model=Pagination[Manga])
async def get_manga_by_genre(
    genre_id: int = Query(...),
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
) -> Pagination[Manga]:
    
    return await cache.get_or_compute(
        key=f"genre:{genre_id}:{limit}:{offset}",
        fetch_func=lambda: manga_model.get_manga_by_genre(genre_id, limit, offset, conn),
        response_model=Pagination[Manga]
    )

@router.get("/genres", response_model=Pagination[Genre])
async def get_all_genres(
    limit: int = Query(default=256, ge=0),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await cache.get_or_compute(
        key=f"all_genres:{limit}:{offset}",
        fetch_func=lambda: genre_model.fetch_genres(limit, offset, conn),
        response_model=Pagination[Genre]
    )