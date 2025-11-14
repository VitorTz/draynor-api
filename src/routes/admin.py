from fastapi import APIRouter, Depends, Query
from fastapi.exceptions import HTTPException
from src.security import require_admin
from src.db import get_db
from asyncpg import Connection
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


@router.get("/count")
async def get_db_count(conn: Connection = Depends(get_db)):
    num_mangas = await conn.fetchval("SELECT COUNT(*) FROM mangas")
    num_chapters = await conn.fetchval("SELECT COUNT(*) FROM chapters")
    num_chapter_images = await conn.fetchval("SELECT COUNT(*) FROM chapter_images")

    return {
        "num_mangas": num_mangas,
        "num_chapters": num_chapters,
        "num_chapter_images": num_chapter_images
    }


@router.get("/table/backup")
async def get_table_backup(
    table_name: str = Query(...),
    conn: Connection = Depends(get_db)
):
    try:        
        # Obter informações das colunas
        columns_query = text("""
            SELECT 
                column_name, 
                data_type
            FROM 
                information_schema.columns
            WHERE table_name = :table_name
            ORDER BY ordinal_position
        """)
        columns_result = conn.execute(columns_query, {"table_name": table_name})
        columns = [row[0] for row in columns_result]
        
        if not columns:
            raise HTTPException(
                status_code=400,
                detail=f"Não foi possível obter as colunas da tabela '{table_name}'"
            )
        
        # Obter os dados da tabela
        select_query = text(f'SELECT * FROM "{table_name}"')
        data_result = conn.execute(select_query)
        rows = data_result.fetchall()
        
        # Gerar o arquivo SQL
        sql_output = StringIO()
        
        # Cabeçalho do arquivo
        sql_output.write(f"-- Backup da tabela: {table_name}\n")
        sql_output.write(f"-- Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        sql_output.write(f"-- Total de registros: {len(rows)}\n\n")
        
        # Gerar INSERTs
        column_names = ", ".join([f'"{col}"' for col in columns])
        
        for row in rows:
            values = []
            for value in row:
                if value is None:
                    values.append("NULL")
                elif isinstance(value, str):
                    # Escapar aspas simples
                    escaped_value = value.replace("'", "''")
                    values.append(f"'{escaped_value}'")
                elif isinstance(value, (int, float)):
                    values.append(str(value))
                elif isinstance(value, bool):
                    values.append("TRUE" if value else "FALSE")
                elif isinstance(value, datetime):
                    values.append(f"'{value.isoformat()}'")
                else:
                    # Para outros tipos, converter para string e escapar
                    str_value = str(value).replace("'", "''")
                    values.append(f"'{str_value}'")
            
            values_str = ", ".join(values)
            sql_output.write(f'INSERT INTO "{table_name}" ({column_names}) VALUES ({values_str});\n')
        
        # Preparar o conteúdo para download
        sql_content = sql_output.getvalue()
        sql_output.close()
        
        # Criar um stream para o arquivo
        file_stream = StringIO(sql_content)
        
        # Retornar como arquivo para download
        filename = f"backup_{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        return StreamingResponse(
            iter([file_stream.getvalue()]),
            media_type="application/sql",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar backup da tabela: {str(e)}"
        )