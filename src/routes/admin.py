from fastapi import APIRouter, Depends
from src.security import require_admin
import platform
import psutil
import time


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/health")
def admin_health():
    return {
        "status": "ok",
        "server_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "python_version": platform.python_version(),
        "platform": platform.system(),
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "memory": {
            "total_mb": round(psutil.virtual_memory().total / (1024 * 1024)),
            "used_mb": round(psutil.virtual_memory().used / (1024 * 1024)),
            "percent": psutil.virtual_memory().percent
        },
        "disk": {
            "total_gb": round(psutil.disk_usage('/').total / (1024**3)),
            "used_gb": round(psutil.disk_usage('/').used / (1024**3)),
            "percent": psutil.disk_usage('/').percent
        },
        "uptime_seconds": round(time.time() - psutil.boot_time(), 2)
    }