from src.schemas.bug_report import BugReport, BugReportCreate
from fastapi import APIRouter, Depends, Query, status
from src.models import bug_report as bug_report_model
from src.db import get_db
from asyncpg import Connection


router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=BugReport)
async def create_bug_report(
    bug_report: BugReportCreate,
    conn: Connection = Depends(get_db)
) -> BugReportCreate:
    return await bug_report_model.create_bug_report(bug_report, conn)
