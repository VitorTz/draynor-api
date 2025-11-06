from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from src.security import require_admin
from src.schemas.chapter import ChapterImageList, ChapterImage, ChapterImageCreate, ChapterImageDelete, ChapterImageListCreate
from src.models import chapter_images as chapter_images_model
from src.schemas.general import Pagination, IntId
from src.db import get_db
from asyncpg import Connection


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/", status_code=status.HTTP_200_OK, response_model=ChapterImageList)
async def get_chapter_images(chapter: IntId, conn: Connection = Depends(get_db)):
    return await chapter_images_model.get_chapter_images(chapter, conn)


@router.get("/all", status_code=status.HTTP_200_OK, response_model=Pagination[ChapterImage])
async def get_all_chapter_images(
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db)
):
    return await chapter_images_model.get_all_chapter_images(limit, offset, conn)


@router.post("/single", status_code=status.HTTP_201_CREATED)
async def create_chapter_image(chapter_image: ChapterImageCreate, conn: Connection = Depends(get_db)):
    await chapter_images_model.create_chapter_image(chapter_image, conn)
    return Response()


@router.post("/all", status_code=status.HTTP_201_CREATED)
async def create_chapter_image(chapter_images: ChapterImageListCreate, conn: Connection = Depends(get_db)):
    await chapter_images_model.create_chapter_images(chapter_images, conn)
    return Response()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chapter_image(chapter_image: ChapterImageDelete, conn: Connection = Depends(get_db)):
    await chapter_images_model.delete_chapter_image(chapter_image, conn)


@router.delete("/chapter", status_code=status.HTTP_204_NO_CONTENT)
async def delete_images_from_chapter(chapter: IntId, conn: Connection = Depends(get_db)):
    await chapter_images_model.delete_chapter_images(chapter, conn)