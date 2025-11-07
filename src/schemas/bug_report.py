from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime


BugReportLiteral = Literal[
    'UI', 
    'Backend', 
    'Performance', 
    'Security', 
    'Database',
    'Network', 
    'Crash', 
    'Logic', 
    'Compatibility', 
    'Other'
]



class BugReport(BaseModel):

    id: int
    title: str
    descr: Optional[str]
    bug_type: BugReportLiteral
    created_at: datetime



class BugReportCreate(BaseModel):

    title: str
    descr: Optional[str] = None
    bug_type: BugReportLiteral