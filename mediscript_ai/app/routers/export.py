from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.export_service import generate_prescription_pdf


router = APIRouter(prefix="/export", tags=["export"])


@router.get("/prescription/{prescription_id}")
def export_prescription_pdf(prescription_id: int, db: Session = Depends(get_db)):
    try:
        pdf_bytes = generate_prescription_pdf(db, prescription_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="prescription_{prescription_id}.pdf"'},
    )

