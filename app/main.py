import io
import zipfile
from pathlib import Path

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
)
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from .config import MAX_RECIPIENTS
from .database import Base, engine, get_db
from .models import (
    Certificate,
    CertificateStatus,
    Job,
)
from .processing import create_job, process_job
from .schemas import (
    CertificateOut,
    JobCreate,
    JobOut,
)


def create_app():
    app = FastAPI(
        title="Bulk Certificate Generator API",
        version="1.0.0"
    )

    Base.metadata.create_all(bind=engine)

    def build_job_response(
        db: Session,
        job: Job
    ):
        certificates = (
            db.query(Certificate)
            .filter(
                Certificate.job_id == job.id
            )
            .all()
        )

        succeeded = sum(
            1
            for certificate in certificates
            if certificate.status ==
            CertificateStatus.GENERATED.value
        )

        failed = sum(
            1
            for certificate in certificates
            if certificate.status ==
            CertificateStatus.FAILED.value
        )

        pending = (
            job.total - succeeded - failed
        )

        progress = (
            ((succeeded + failed) / job.total) * 100
            if job.total
            else 0
        )

        certificate_data = []

        for certificate in certificates:

            download_url = None

            if certificate.status == (
                CertificateStatus.GENERATED.value
            ):
                download_url = (
                    f"/certificates/"
                    f"{certificate.id}/download"
                )

            certificate_data.append(
                CertificateOut(
                    id=certificate.id,
                    recipient_name=certificate.recipient_name,
                    email=certificate.email,
                    achievement=certificate.achievement,
                    status=certificate.status,
                    error=certificate.error,
                    download_url=download_url
                )
            )

        return JobOut(
            id=job.id,
            event_name=job.event_name,
            issue_date=job.issue_date,
            status=job.status,
            total=job.total,
            succeeded=succeeded,
            failed=failed,
            pending=pending,
            progress_percent=round(
                progress,
                2
            ),
            certificates=certificate_data
        )

    # -------------------------
    # Home
    # -------------------------

    @app.get("/")
    def root():
        return {
            "message": "Bulk Certificate Generator API is running"
        }

    # -------------------------
    # Create Job
    # -------------------------

    @app.post(
        "/jobs",
        response_model=JobOut,
        status_code=202
    )
    def submit_job(
        request: JobCreate,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
    ):
        if len(request.recipients) > MAX_RECIPIENTS:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"Maximum {MAX_RECIPIENTS} "
                    "recipients allowed."
                )
            )

        job = create_job(
            db,
            request
        )

        background_tasks.add_task(
            process_job,
            job.id
        )

        return build_job_response(
            db,
            job
        )

    # -------------------------
    # Get Job
    # -------------------------

    @app.get(
        "/jobs/{job_id}",
        response_model=JobOut
    )
    def get_job(
        job_id: int,
        db: Session = Depends(get_db)
    ):
        job = db.query(Job).filter(
            Job.id == job_id
        ).first()

        if not job:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )

        return build_job_response(
            db,
            job
        )

    # -------------------------
    # Get Certificates
    # -------------------------

    @app.get(
        "/jobs/{job_id}/certificates",
        response_model=list[CertificateOut]
    )
    def get_certificates(
        job_id: int,
        status: str | None = None,
        db: Session = Depends(get_db)
    ):
        job = db.query(Job).filter(
            Job.id == job_id
        ).first()

        if not job:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )

        query = db.query(
            Certificate
        ).filter(
            Certificate.job_id == job_id
        )

        if status:
            query = query.filter(
                Certificate.status == status
            )

        certificates = query.all()

        return [
            CertificateOut(
                id=certificate.id,
                recipient_name=certificate.recipient_name,
                email=certificate.email,
                achievement=certificate.achievement,
                status=certificate.status,
                error=certificate.error,
                download_url=(
                    f"/certificates/"
                    f"{certificate.id}/download"
                    if certificate.status ==
                    CertificateStatus.GENERATED.value
                    else None
                )
            )
            for certificate in certificates
        ]

    # -------------------------
    # Download One Certificate
    # -------------------------

    @app.get(
        "/certificates/{certificate_id}/download"
    )
    def download_certificate(
        certificate_id: int,
        db: Session = Depends(get_db)
    ):
        certificate = db.query(
            Certificate
        ).filter(
            Certificate.id == certificate_id
        ).first()

        if not certificate:
            raise HTTPException(
                status_code=404,
                detail="Certificate not found"
            )

        if certificate.status != (
            CertificateStatus.GENERATED.value
        ):
            raise HTTPException(
                status_code=409,
                detail="Certificate is not generated yet"
            )

        path = Path(
            certificate.file_path
        )

        if not path.exists():
            raise HTTPException(
                status_code=404,
                detail="Certificate file not found"
            )

        return FileResponse(
            path=str(path),
            media_type="application/pdf",
            filename=path.name
        )

    # -------------------------
    # Download ZIP
    # -------------------------

    @app.get(
        "/jobs/{job_id}/download"
    )
    def download_job(
        job_id: int,
        db: Session = Depends(get_db)
    ):
        job = db.query(Job).filter(
            Job.id == job_id
        ).first()

        if not job:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )

        certificates = db.query(
            Certificate
        ).filter(
            Certificate.job_id == job_id,
            Certificate.status ==
            CertificateStatus.GENERATED.value
        ).all()

        if not certificates:
            raise HTTPException(
                status_code=409,
                detail="No generated certificates available"
            )

        memory_file = io.BytesIO()

        with zipfile.ZipFile(
            memory_file,
            "w",
            zipfile.ZIP_DEFLATED
        ) as zip_file:

            for certificate in certificates:

                path = Path(
                    certificate.file_path
                )

                if path.exists():
                    zip_file.write(
                        path,
                        arcname=path.name
                    )

        memory_file.seek(0)

        return StreamingResponse(
            memory_file,
            media_type="application/zip",
            headers={
                "Content-Disposition":
                    f"attachment; "
                    f"filename=job_{job_id}.zip"
            }
        )

    return app


app = create_app()