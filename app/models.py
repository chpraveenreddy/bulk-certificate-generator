from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class JobStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"
    FAILED = "FAILED"


class CertificateStatus(str, Enum):
    PENDING = "PENDING"
    GENERATED = "GENERATED"
    FAILED = "FAILED"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    event_name = Column(
        String(200),
        nullable=False
    )

    issue_date = Column(
        Date,
        nullable=False
    )

    status = Column(
        String(30),
        nullable=False,
        default=JobStatus.PENDING.value
    )

    total = Column(
        Integer,
        nullable=False,
        default=0
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    certificates = relationship(
        "Certificate",
        back_populates="job",
        cascade="all, delete-orphan"
    )


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    job_id = Column(
        Integer,
        ForeignKey("jobs.id"),
        nullable=False
    )

    recipient_name = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(255),
        nullable=True
    )

    achievement = Column(
        String(200),
        nullable=False,
        default="Participation"
    )

    status = Column(
        String(30),
        nullable=False,
        default=CertificateStatus.PENDING.value
    )

    error = Column(
        Text,
        nullable=True
    )

    file_path = Column(
        Text,
        nullable=True
    )

    raw_data = Column(
        Text,
        nullable=True
    )

    job = relationship(
        "Job",
        back_populates="certificates"
    )