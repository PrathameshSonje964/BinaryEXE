from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.database import get_db
from app.models.models import Prescription, PrescriptionStatusEnum
from app.schemas.schemas import OCRResult
from app.services.handwriting_service import run_handwriting_model


router = APIRouter(prefix="/upload", tags=["upload"])
settings = get_settings()


@router.post("/", response_class=RedirectResponse)
async def upload_prescription(
    file: UploadFile = File(...),
    title: str = Form("Prescription"),
    db: Session = Depends(get_db),
) -> Any:
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are supported")

    uploads_dir = settings.uploads_dir
    uploads_dir.mkdir(parents=True, exist_ok=True)

    file_path = uploads_dir / file.filename
    with open(file_path, "wb") as f:
        f.write(await file.read())

    ocr_result: OCRResult = run_handwriting_model(file_path)

    prescription = Prescription(
        user_id=1,
        title=title,
        raw_text=ocr_result.raw_text,
        image_path=str(file_path),
        confidence_score=ocr_result.ocr_reliability * 100.0,
        status=PrescriptionStatusEnum.NEEDS_REVIEW,
    )
    db.add(prescription)
    db.commit()
    db.refresh(prescription)

    return RedirectResponse(url=f"/workspace/{prescription.id}", status_code=303)

