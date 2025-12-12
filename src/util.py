from fastapi import Request, UploadFile
from pathlib import Path
from asyncpg import Connection
from datetime import datetime, timezone
from src.schemas.general import ClientInfo
from typing import Optional, Any
from PIL import Image
from threading import Lock
from functools import wraps
from io import BytesIO
from PIL import Image
import colorsys
import unicodedata
import requests
import uuid
import re
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


def download_resize_to_webp(url: str, output_path: str, max_width: int = 720) -> Path:
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()

    img = Image.open(io.BytesIO(resp.content))
    
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)
    
    img = img.convert("RGB")
    img.save(output_path, "WEBP", quality=90)    


def normalize_dirname(name: str) -> str:    
    # Normalize and remove accents
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))

    # Replace Windows-invalid characters and any control chars
    invalid = r'[<>:"/\\|?*\x00-\x1F]'
    name = re.sub(invalid, "_", name)

    # Replace spaces with underscore
    name = re.sub(r"\s+", "_", name)

    # Collapse repeated underscores
    name = re.sub(r"_+", "_", name)

    # Remove leading/trailing spaces, dots, underscores
    name = name.strip(" ._")

    # Windows reserved names
    reserved = {
        "CON", "PRN", "AUX", "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }
    if name.upper() in reserved:
        name = f"_{name}"

    # Default fallback
    if not name:
        name = "dir"

    return name


def normalize_to_url(text: str) -> str:    
    # unicode normalize
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))

    # lowercase
    text = text.lower()

    # replace invalid characters with '-'
    text = re.sub(r"[^a-z0-9\-._~]", "-", text)

    # collapse multiple '-'
    text = re.sub(r"-+", "-", text)

    # strip leading/trailing '-'
    text = text.strip("-")

    # fallback if empty
    if not text:
        text = "item"

    return text


def singleton(cls):
    instances = {}
    lock = Lock()

    @wraps(cls)
    def get_instance(*args, **kwargs):        
        if cls not in instances:
            with lock:                
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance


def get_manga_dominant_color(image_url: str) -> str:
    
    try:
        # 1. Download da imagem (timeout para não travar a API)
        response = requests.get(image_url, timeout=5)
        response.raise_for_status()
        
        # 2. Abre a imagem e converte para RGB (evita problemas com PNGs transparentes)
        img = Image.open(BytesIO(response.content)).convert("RGB")
        
        # 3. Redimensiona para acelerar o processamento (100x100 é suficiente)
        img.thumbnail((100, 100))
        
        # 4. Quantização: Reduz a imagem para apenas 10 cores principais
        # Isso agrupa pixels similares
        paletted = img.quantize(colors=10, method=2) 
        
        # Pega a paleta (lista de RGBs: [r, g, b, r, g, b...])
        palette = paletted.getpalette()
        
        # Conta a frequência de cada cor
        color_counts = paletted.getbbox()
        if not color_counts:
             # Fallback se a imagem for vazia ou sólida
             return "#333333"

        # Recupera as cores mais frequentes
        # getcolors retorna uma lista de tuplas (frequencia, indice_da_cor)
        colors = paletted.getcolors()
        
        best_color = (0, 0, 0)
        max_score = -1

        for count, index in colors:
            
            r = palette[index * 3]
            g = palette[index * 3 + 1]
            b = palette[index * 3 + 2]
                        
            h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
            
            if v < 0.15: continue 
            if v > 0.95 and s < 0.10: continue
            
            score = (s * 3.0) + (v * 1.0) + (count / (100*100) * 0.5)
            
            if score > max_score:
                max_score = score
                best_color = (r, g, b)

        # Se nenhuma cor passou no filtro (ex: mangá preto e branco), pega a mais frequente mesmo
        if max_score == -1:
             # Pega a cor mais frequente (última da lista ordenada pelo sort padrão do getcolors)
             top_index = sorted(colors, reverse=True)[0][1]
             r = palette[top_index * 3]
             g = palette[top_index * 3 + 1]
             b = palette[top_index * 3 + 2]
             best_color = (r, g, b)

        # Retorna em Hex
        return '#{:02x}{:02x}{:02x}'.format(*best_color)
    except Exception as e:
        print(f"Erro ao extrair cor da imagem {image_url}: {e}")
        raise e