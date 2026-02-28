from datetime import date, datetime, time, timedelta
from typing import List

from sqlalchemy.orm import Session

from app.models.models import Dose, Medicine, Prescription


def generate_schedule_for_prescription(db: Session, prescription: Prescription) -> List[Dose]:
    doses: List[Dose] = []
    today = date.today()

    for med in prescription.medicines:
        assert isinstance(med, Medicine)
        if med.duration_days is None or med.duration_days <= 0:
            continue

        per_day = 0
        if med.frequency:
            freq = med.frequency.upper()
            if freq == "OD":
                per_day = 1
            elif freq == "BD":
                per_day = 2
            elif freq == "TDS":
                per_day = 3
            elif freq == "QID":
                per_day = 4

        if per_day <= 0:
            per_day = 3

        times: List[time] = []
        if per_day == 1:
            times = [time(8, 0)]
        elif per_day == 2:
            times = [time(8, 0), time(20, 0)]
        elif per_day == 3:
            times = [time(8, 0), time(14, 0), time(20, 0)]
        elif per_day == 4:
            times = [time(6, 0), time(12, 0), time(18, 0), time(22, 0)]

        for day_offset in range(med.duration_days):
            dose_date = today + timedelta(days=day_offset)
            for t in times:
                dose = Dose(
                    prescription_id=prescription.id,
                    medicine_id=med.id,
                    date=dose_date,
                    time=t,
                    taken=False,
                )
                db.add(dose)
                doses.append(dose)

    db.commit()
    db.refresh(prescription)
    return doses

