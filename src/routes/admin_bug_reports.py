from src.schemas.bug_report import BugReport, BugReportCreate, BugReportLiteral
from src.schemas.general import Pagination, IntId
from src.security import require_admin
from fastapi import APIRouter, Depends, Query, status
from src.models import bug_report as bug_report_model
from src.db import get_db
from asyncpg import Connection
from typing import Optional


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/", status_code=status.HTTP_200_OK, response_model=Pagination[BugReport])
async def get_bug_reports(
    limit: int = Query(default=64, ge=0, le=64),
    offset: int = Query(default=0, ge=0),
    bug_type: Optional[BugReportLiteral] = Query(default=None),
    conn: Connection = Depends(get_db)
) -> Pagination[BugReport]:
    return await bug_report_model.get_bug_reports(
        limit, 
        offset, 
        bug_type, 
        conn
    )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=BugReport)
async def create_bug_report(
    bug_report: BugReportCreate,
    conn: Connection = Depends(get_db)
) -> BugReportCreate:
    return await bug_report_model.create_bug_report(bug_report, conn)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bug_report(bug_report: IntId, conn: Connection = Depends(get_db)):
    await bug_report_model.delete_bug_report(bug_report, conn)