from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Dose


router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.post("/doses/{dose_id}/toggle")
def toggle_dose_taken(dose_id: int, db: Session = Depends(get_db)) -> Any:
    dose = db.query(Dose).filter(Dose.id == dose_id).first()
    if not dose:
        raise HTTPException(status_code=404, detail="Dose not found")

    from datetime import datetime

    dose.taken = not dose.taken
    dose.taken_at = datetime.utcnow() if dose.taken else None
    db.commit()
    return {"id": dose.id, "taken": dose.taken}

