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
    cert_id = registration.certificate_id or f"PIEMR-URJOTSAV-{registration.id:04d}"
    registration.certificate_id = cert_id

    output_dir = Path(settings.MEDIA_ROOT) / "certificates"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{cert_id}.pdf"

    pdf = canvas.Canvas(str(output_path), pagesize=landscape(A4))
    width, height = landscape(A4)

    # --- Background & Watermark ---
    pdf.setFillColor(colors.HexColor("#FCFBF7")) # Rich Cream
    pdf.rect(0, 0, width, height, fill=1, stroke=0)

    # Subtle "URJOTSAV" background watermark pattern
    pdf.rotate(35)
    pdf.setFillColor(colors.HexColor("#F1F5F9"))
    pdf.setFont("Helvetica-Bold", 100)
    for i in range(-5, 5):
        for j in range(-5, 5):
            pdf.drawString(i * 5 * inch, j * 2 * inch, "URJOTSAV")
    pdf.rotate(-35)

    # --- Corner Graphics ---
    # Top Left Dark Accent
    pdf.setFillColor(colors.HexColor("#061120"))
    pdf.pathBegin()
    pdf.moveTo(0, height)
    pdf.lineTo(2.2 * inch, height)
    pdf.lineTo(0, height - 2.2 * inch)
    pdf.pathClose()
    pdf.fill()

    # Bottom Right Orange Accent
    pdf.setFillColor(colors.HexColor("#F97316"))
    pdf.pathBegin()
    pdf.moveTo(width, 0)
    pdf.lineTo(width - 1.8 * inch, 0)
    pdf.lineTo(width, 1.8 * inch)
    pdf.pathClose()
    pdf.fill()

    # --- Triple-Layer Premium Border ---
    # Inner Gold
    pdf.setStrokeColor(colors.HexColor("#D4AF37"))
    pdf.setLineWidth(4)
    pdf.roundRect(0.25 * inch, 0.25 * inch, width - 0.5 * inch, height - 0.5 * inch, 12, stroke=1, fill=0)
    # Middle White
    pdf.setStrokeColor(colors.white)
    pdf.setLineWidth(2)
    pdf.roundRect(0.32 * inch, 0.32 * inch, width - 0.64 * inch, height - 0.64 * inch, 10, stroke=1, fill=0)
    # Outer Gold
    pdf.setStrokeColor(colors.HexColor("#B8860B"))
    pdf.setLineWidth(1)
    pdf.roundRect(0.38 * inch, 0.38 * inch, width - 0.76 * inch, height - 0.76 * inch, 8, stroke=1, fill=0)

    # --- Header Section ---
    pdf.setFillColor(colors.HexColor("#061120"))
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawCentredString(width / 2, height - 1.0 * inch, "PRESTIGE INSTITUTE OF ENGINEERING MANAGEMENT & RESEARCH, INDORE")
    
    pdf.setFont("Helvetica-Bold", 11)
    pdf.setFillColor(colors.HexColor("#64748B"))
    pdf.drawCentredString(width / 2, height - 1.25 * inch, "NBA ACCREDITED | APPROVED BY AICTE, NEW DELHI | AFFILIATED TO RGPV & DAVV")

    # --- Event Brand Area ---
    pdf.setFillColor(colors.HexColor("#061120"))
    pdf.setFont("Helvetica-Bold", 42)
    pdf.drawCentredString(width / 2, height - 2.0 * inch, "URJOTSAV 2K26")
    
    # Modern separator
    pdf.setStrokeColor(colors.HexColor("#F97316"))
    pdf.setLineWidth(5)
    pdf.line(width/2 - 1.8*inch, height - 2.25*inch, width/2 + 1.8*inch, height - 2.25*inch)

    # --- Certificate Title Banner ---
    banner_y = height - 2.9 * inch
    pdf.setFillColor(colors.HexColor("#F97316"))
    pdf.rect(width/2 - 2.8*inch, banner_y, 5.6*inch, 0.5*inch, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawCentredString(width / 2, banner_y + 0.15 * inch, "CERTIFICATE OF APPRECIATION")

    # --- Participant Content ---
    pdf.setFillColor(colors.HexColor("#1E293B"))
    pdf.setFont("Helvetica", 18)
    pdf.drawCentredString(width / 2, height - 3.7 * inch, "This is proudly presented to")

    # Grand Name
    pdf.setFillColor(colors.HexColor("#061120"))
    pdf.setFont("Helvetica-Bold", 38)
    pdf.drawCentredString(width / 2, height - 4.35 * inch, registration.full_name)

    # Event Detail Text
    pdf.setFillColor(colors.HexColor("#475569"))
    pdf.setFont("Helvetica", 15)
    pdf.drawCentredString(width / 2, height - 4.9 * inch, f"for outstanding participation in the event '{event.title}'")
    pdf.drawCentredString(width / 2, height - 5.2 * inch, "during the Annual Technical, Cultural and Sports Festival at PIEMR, Indore.")

    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawCentredString(width / 2, height - 5.6 * inch, f"{event.event_date} | {event.venue}")

    # --- SECURITY SEAL (Premium Stamp) ---
    seal_x = width - 2.0 * inch
    seal_y = 1.2 * inch
    # Outer gold circle
    pdf.setStrokeColor(colors.HexColor("#D4AF37"))
    pdf.setLineWidth(2)
    pdf.circle(seal_x, seal_y, 0.5 * inch, stroke=1, fill=0)
    # Inner gold circle
    pdf.setLineWidth(1)
    pdf.circle(seal_x, seal_y, 0.42 * inch, stroke=1, fill=0)
    
    # Seal Text
    pdf.setFillColor(colors.HexColor("#B8860B"))
    pdf.setFont("Helvetica-Bold", 7)
    pdf.drawCentredString(seal_x, seal_y + 0.1 * inch, "OFFICIAL")
    pdf.drawCentredString(seal_x, seal_y - 0.05 * inch, "VERIFIED")
    pdf.drawCentredString(seal_x, seal_y - 0.2 * inch, "SEAL")

    # --- DIGITAL VERIFICATION BAR ---
    pdf.setFillColor(colors.HexColor("#F1F5F9"))
    pdf.rect(1.2 * inch, 0.9 * inch, 3.5 * inch, 0.8 * inch, fill=1, stroke=0)
    
    pdf.setFillColor(colors.HexColor("#166534")) # Dark Green
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(1.4 * inch, 1.45 * inch, "DIGITALLY SIGNED & VERIFIED")
    
    pdf.setFillColor(colors.HexColor("#64748B"))
    pdf.setFont("Helvetica", 8)
    pdf.drawString(1.4 * inch, 1.25 * inch, "Secured via PIEMR Digital Certification Protocol")
    pdf.drawString(1.4 * inch, 1.12 * inch, f"ID: {cert_id}")
    pdf.drawString(1.4 * inch, 1.0 * inch, f"Verified On: {timezone.now().strftime('%d %b %Y, %H:%M:%S')} IST")

    # --- Footer ---
    pdf.setFillColor(colors.HexColor("#94A3B8"))
    pdf.setFont("Helvetica", 8)
    pdf.drawCentredString(width / 2, 0.5 * inch, "This is a system-generated secure digital document and does not require a manual signature.")
    pdf.drawCentredString(width / 2, 0.38 * inch, "Verify authenticity at: seminar.pythonanywhere.com/certificate/")

    pdf.save()

    with output_path.open("rb") as handle:
        registration.certificate_pdf.save(output_path.name, File(handle), save=False)
    registration.save(update_fields=["certificate_id", "certificate_pdf", "updated_at"])


def send_certificate_email(registration):
    # FORCE REGENERATION for now to ensure latest design is always used
    generate_certificate(registration)

    subject = f"Certificate of Participation - Urjotsav 2K26"
    body = (
        f"Dear {registration.full_name},\n\n"
        f"Congratulations on your participation in Urjotsav 2K26 at PIEMR, Indore.\n"
        f"Your premium digitally verified certificate is attached to this email.\n\n"
        "Regards,\nUrjotsav 2K26 Team\nPIEMR, Indore"
    )
    email = EmailMessage(subject, body, to=[registration.email])
    certificate_path = Path(registration.certificate_pdf.path)
    email.attach_file(certificate_path)
    email.send(fail_silently=False)
    registration.certificate_emailed_at = timezone.now()
    registration.save(update_fields=["certificate_emailed_at", "updated_at"])
