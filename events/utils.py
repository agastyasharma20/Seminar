from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.mail import EmailMessage
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from .models import EventSettings


def get_event_settings():
    event, _ = EventSettings.objects.get_or_create(pk=1)
    return event


def generate_certificate(registration):
    event = registration.event
    cert_id = registration.certificate_id or f"PIEMR-WASVT-{registration.id:04d}"
    registration.certificate_id = cert_id

    output_dir = Path(settings.MEDIA_ROOT) / "certificates"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{cert_id}.pdf"

    pdf = canvas.Canvas(str(output_path), pagesize=landscape(A4))
    width, height = landscape(A4)

    pdf.setFillColor(colors.HexColor("#061120"))
    pdf.rect(0, 0, width, height, fill=1, stroke=0)
    pdf.setFillColor(colors.HexColor("#0ea5e9"))
    pdf.rect(0, height - 0.18 * inch, width, 0.18 * inch, fill=1, stroke=0)
    pdf.setFillColor(colors.HexColor("#22c55e"))
    pdf.rect(0, 0, width, 0.12 * inch, fill=1, stroke=0)

    margin = 0.52 * inch
    pdf.setStrokeColor(colors.HexColor("#38bdf8"))
    pdf.setLineWidth(2)
    pdf.roundRect(margin, margin, width - 2 * margin, height - 2 * margin, 18, stroke=1, fill=0)

    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawCentredString(width / 2, height - 1.05 * inch, event.organizer)
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.HexColor("#bae6fd"))
    pdf.drawCentredString(width / 2, height - 1.28 * inch, f"Organized by {event.organized_by}")
    pdf.setFillColor(colors.HexColor("#bae6fd"))
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(width / 2, height - 1.55 * inch, "Certificate of Participation")

    pdf.setFillColor(colors.HexColor("#dbeafe"))
    pdf.setFont("Helvetica", 13)
    pdf.drawCentredString(width / 2, height - 2.0 * inch, "This is to certify that")

    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawCentredString(width / 2, height - 2.55 * inch, registration.full_name)

    pdf.setFillColor(colors.HexColor("#dbeafe"))
    pdf.setFont("Helvetica", 13)
    pdf.drawCentredString(width / 2, height - 3.03 * inch, "has participated in the national seminar")

    pdf.setFillColor(colors.HexColor("#67e8f9"))
    pdf.setFont("Helvetica-Bold", 17)
    pdf.drawCentredString(width / 2, height - 3.5 * inch, event.title)

    pdf.setFillColor(colors.HexColor("#cbd5e1"))
    pdf.setFont("Helvetica", 11)
    pdf.drawCentredString(width / 2, height - 3.9 * inch, f"Expert: {event.expert_name}")
    pdf.drawCentredString(width / 2, height - 4.18 * inch, event.expert_title)
    pdf.drawCentredString(width / 2, height - 4.55 * inch, f"{event.event_date} | {event.event_time}")
    pdf.drawCentredString(width / 2, height - 4.84 * inch, event.venue)

    pdf.setStrokeColor(colors.HexColor("#38bdf8"))
    pdf.line(1.15 * inch, 1.3 * inch, 3.15 * inch, 1.3 * inch)
    pdf.line(width - 3.15 * inch, 1.3 * inch, width - 1.15 * inch, 1.3 * inch)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawCentredString(2.15 * inch, 1.04 * inch, "Event Coordinator")
    pdf.drawCentredString(width - 2.15 * inch, 1.04 * inch, "Authorized Signatory")

    pdf.setFillColor(colors.HexColor("#94a3b8"))
    pdf.setFont("Helvetica", 9)
    pdf.drawCentredString(width / 2, 0.78 * inch, f"Certificate ID: {cert_id}")
    pdf.save()

    with output_path.open("rb") as handle:
        registration.certificate_pdf.save(output_path.name, File(handle), save=False)
    registration.save(update_fields=["certificate_id", "certificate_pdf", "updated_at"])


def send_certificate_email(registration):
    if not registration.certificate_pdf or not Path(registration.certificate_pdf.path).exists():
        generate_certificate(registration)

    subject = f"Certificate of Participation - {registration.event.title}"
    body = (
        f"Dear {registration.full_name},\n\n"
        f"Thank you for participating in {registration.event.title} at PIEMR, Indore.\n"
        f"Your certificate ID is {registration.certificate_id}. The certificate PDF is attached.\n\n"
        "Regards,\nPIEMR Event Team"
    )
    email = EmailMessage(subject, body, to=[registration.email])
    certificate_path = Path(registration.certificate_pdf.path)
    email.attach_file(certificate_path)
    email.send(fail_silently=False)
    registration.certificate_emailed_at = timezone.now()
    registration.save(update_fields=["certificate_emailed_at", "updated_at"])
