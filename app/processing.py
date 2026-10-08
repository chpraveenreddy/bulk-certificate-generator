import json
import re
from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from .config import STORAGE_DIR
from .generator import render_certificate
from .models import (
    Certificate,
    CertificateStatus,
    Job,
    JobStatus,
)
from .schemas import JobCreate


EMAIL_PATTERN = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)


def validate_recipient(recipient):
    errors = []

    name = recipient.name.strip()

    if not name:
        errors.append("Name is required.")

    if len(name) > 100:
        errors.append(
            "Name must not exceed 100 characters."
        )

    if recipient.email:
        email = recipient.email.strip()

        if not EMAIL_PATTERN.match(email):
            errors.append(
                "Invalid email format."
            )

    return errors


def create_job(
    db: Session,
    request: JobCreate
):
    issue_date = request.issue_date or date.today()

    job = Job(
        event_name=request.event_name.strip(),
        issue_date=issue_date,
        status=JobStatus.PENDING.value,
        total=len(request.recipients)
    )

    db.add(job)
    db.flush()

    for recipient in request.recipients:

        errors = validate_recipient(recipient)

        certificate_status = (
            CertificateStatus.FAILED.value
            if errors
            else CertificateStatus.PENDING.value
        )

        certificate = Certificate(
            job_id=job.id,
            recipient_name=recipient.name.strip(),
            email=(
                recipient.email.strip()
                if recipient.email
                else None
            ),
            achievement=(
                recipient.achievement
                or "Participation"
            ),
            status=certificate_status,
            error=(
                "; ".join(errors)
                if errors
                else None
            ),
            raw_data=json.dumps(
                recipient.model_dump()
            )
        )

        db.add(certificate)

    db.commit()
    db.refresh(job)

    return job


def process_job(job_id: int):
    from .database import SessionLocal

    db = SessionLocal()

    try:
        job = db.query(Job).filter(
            Job.id == job_id
        ).first()

        if not job:
            return

        job.status = JobStatus.PROCESSING.value
        db.commit()

        certificates = (
            db.query(Certificate)
            .filter(
                Certificate.job_id == job_id,
                Certificate.status ==
                CertificateStatus.PENDING.value
            )
            .all()
        )

        job_directory = (
            Path(STORAGE_DIR)
            / f"job_{job_id}"
        )

        job_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        for certificate in certificates:

            try:
                # Create a safe filename from recipient name
                safe_name = re.sub(
                    r"[^A-Za-z0-9]+",
                    "_",
                    certificate.recipient_name
                ).strip("_")

                # Fallback if name is somehow empty
                if not safe_name:
                    safe_name = (
                        f"certificate_{certificate.id}"
                    )

                output_path = (
                    job_directory
                    / f"{safe_name}.pdf"
                )

                render_certificate(
                    output_path=str(output_path),
                    event_name=job.event_name,
                    issue_date=str(job.issue_date),
                    recipient_name=certificate.recipient_name,
                    achievement=certificate.achievement
                )

                certificate.status = (
                    CertificateStatus.GENERATED.value
                )

                certificate.file_path = str(
                    output_path
                )

                certificate.error = None

            except Exception as exc:

                certificate.status = (
                    CertificateStatus.FAILED.value
                )

                certificate.error = str(exc)

            db.commit()

        successful = db.query(
            Certificate
        ).filter(
            Certificate.job_id == job_id,
            Certificate.status ==
            CertificateStatus.GENERATED.value
        ).count()

        failed = db.query(
            Certificate
        ).filter(
            Certificate.job_id == job_id,
            Certificate.status ==
            CertificateStatus.FAILED.value
        ).count()

        if successful == job.total:

            job.status = (
                JobStatus.COMPLETED.value
            )

        elif successful > 0:

            job.status = (
                JobStatus.COMPLETED_WITH_ERRORS.value
            )

        else:

            job.status = (
                JobStatus.FAILED.value
            )

        db.commit()

    except Exception:

        job = db.query(Job).filter(
            Job.id == job_id
        ).first()

        if job:
            job.status = JobStatus.FAILED.value
            db.commit()

    finally:
        db.close()