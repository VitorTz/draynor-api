from fastapi import Request, UploadFile
from pathlib import Path
from asyncpg import Connection
from datetime import datetime, timezone
from src.schemas.general import ClientInfo
from typing import Optional, Any
from PIL import Image
import uuid
import io


async def execute_sql_file(file: Path, conn: Connection) -> None:
    try:
        with open(file, "r", encoding="utf-8") as f:
            sql_commands = f.read()
        await conn.execute(sql_commands)
    except Exception as e:
        print(f"[EXCEPTION WHEN OPEN COMMANDS] [{file}] | {e}")


def get_client_identifier(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    return request.client.host


def seconds_until(target: datetime) -> int:
    if target.tzinfo is None:
        target = target.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    diff = (target - now).total_seconds()
    return int(diff) if diff > 0 else 0


def get_client_info(request: Request):
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent")
    device_name = None
    if user_agent:
        if "Windows" in user_agent:
            device_name = "Windows PC"
        elif "Macintosh" in user_agent:
            device_name = "Mac"
        elif "Linux" in user_agent:
            device_name = "Linux"
        elif "iPhone" in user_agent:
            device_name = "iPhone"
        elif "Android" in user_agent:
            device_name = "Android"

    return ClientInfo(
        client_ip=client_ip, 
        user_agent=user_agent, 
        device_name=device_name
    )


def coalesce(a: Optional[Any], b: Optional[Any]) -> Optional[Any]:
    if a: return a
    return b


def generate_uuid() -> str:
    return str(uuid.uuid4())


async def convert_upload_to_webp(file: UploadFile, quality: int = 80) -> io.BytesIO:
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))

    buffer = io.BytesIO()
    image.save(buffer, format="WEBP", quality=quality, method=6)
    buffer.seek(0)

    return buffer