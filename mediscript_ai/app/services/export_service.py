from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.models.models import Prescription


def generate_prescription_pdf(db: Session, prescription_id: int) -> bytes:
    prescription = db.query(Prescription).get(prescription_id)
    if not prescription:
        raise ValueError("Prescription not found")

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    pdf.setTitle(f"Prescription #{prescription_id}")
    pdf.drawString(50, height - 50, f"Prescription: {prescription.title}")
    pdf.drawString(50, height - 70, f"Status: {prescription.status}")
    pdf.drawString(50, height - 90, f"Confidence: {prescription.confidence_score:.1f}%")

    y = height - 130
    pdf.drawString(50, y, "Medicines:")
    y -= 20

    for med in prescription.medicines:
        line = f"- {med.normalized_name} ({med.dose}), {med.frequency} for {med.duration_days} days"
        pdf.drawString(60, y, line)
        y -= 15
        if y < 50:
            pdf.showPage()
            y = height - 50

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer.read()

