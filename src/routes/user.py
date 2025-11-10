from fastapi import APIRouter, Depends, status, Request, UploadFile, File
from fastapi.exceptions import HTTPException
from src.schemas.general import Pagination, ImageUrl
from src.schemas.user import User, UserUpdate
from src.models import user as user_model
from src.db import get_db
from src.cloudflare import CloudflareR2Bucket
from asyncpg import Connection, UniqueViolationError
from src import security
from src import util
import io


router = APIRouter()


@router.put("/", status_code=status.HTTP_201_CREATED, response_model=User)
async def update_user_perfil(
    user_update: UserUpdate,
    user: User = Depends(security.get_user_from_token),
    conn: Connection = Depends(get_db)
):
    try:
        return await user_model.update_user(user, user_update, conn)
    except UniqueViolationError as e:
        if 'username' in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")


@router.post("/image/perfil", status_code=status.HTTP_201_CREATED, response_model=ImageUrl)
async def update_user_perfil_image(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(security.get_user_from_token),
    conn: Connection = Depends(get_db),
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{file.content_type}'. Only images are allowed."
        )

    r2: CloudflareR2Bucket = request.app.state.r2
    image_key: str = f"draynor/users/images/perfil/{util.generate_uuid()}.webp"
    image_data: io.BytesIO = await util.convert_upload_to_webp(file)
    perfil_image_url: str = await r2.upload_bytes(image_key, image_data, content_type="image/webp")
    if not perfil_image_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="It was not possible to upload your image."
        )
    
    await user_model.update_user_perfil_image_urll(user, perfil_image_url, conn)
    return { "url": perfil_image_url}


@router.delete("/image/perfil", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_perfil_image(
    request: Request,
    user: User = Depends(security.get_user_from_token),
    conn: Connection = Depends(get_db)
):
    if not user.perfil_image_url: return
    r2: CloudflareR2Bucket = request.app.state.r2
    image_key: str = r2.extract_key(user.perfil_image_url)
    await r2.delete_file(image_key)
    await user_model.update_user_perfil_image_urll(user, None, conn)