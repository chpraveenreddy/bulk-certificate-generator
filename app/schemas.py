from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class RecipientIn(BaseModel):
    name: str
    email: Optional[str] = None
    achievement: Optional[str] = "Participation"


class JobCreate(BaseModel):
    event_name: str = Field(..., max_length=200)
    issue_date: Optional[date] = None

    recipients: List[RecipientIn] = Field(
        ...,
        min_length=1
    )


class CertificateOut(BaseModel):
    id: int
    recipient_name: str
    email: Optional[str]
    achievement: str
    status: str
    error: Optional[str]
    download_url: Optional[str]

    class Config:
        from_attributes = True


class JobOut(BaseModel):
    id: int
    event_name: str
    issue_date: date
    status: str
    total: int
    succeeded: int
    failed: int
    pending: int
    progress_percent: float
    certificates: List[CertificateOut]