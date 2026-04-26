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
    # Sophisticated cream background
    pdf.setFillColor(colors.HexColor("#FCFBF7"))
    pdf.rect(0, 0, width, height, fill=1, stroke=0)

    # Subtle Watermark
    pdf.rotate(35)
    pdf.setFillColor(colors.HexColor("#F1F5F9"))
    pdf.setFont("Helvetica-Bold", 100)
    pdf.drawString(2 * inch, 0, "URJOTSAV 2K26")
    pdf.rotate(-35)

    # Stylish Corner Accents (Blue & Orange)
    pdf.setFillColor(colors.HexColor("#061120")) # Dark Blue
    pdf.pathBegin()
    pdf.moveTo(0, height)
    pdf.lineTo(1.8 * inch, height)
    pdf.lineTo(0, height - 1.8 * inch)
    pdf.pathClose()
    pdf.fill()

    pdf.setFillColor(colors.HexColor("#F97316")) # Orange
    pdf.pathBegin()
    pdf.moveTo(width, 0)
    pdf.lineTo(width - 1.5 * inch, 0)
    pdf.lineTo(width, 1.5 * inch)
    pdf.pathClose()
    pdf.fill()

    # Main Border (Premium Gold)
    pdf.setStrokeColor(colors.HexColor("#D4AF37"))
    pdf.setLineWidth(3)
    pdf.roundRect(0.25 * inch, 0.25 * inch, width - 0.5 * inch, height - 0.5 * inch, 10, stroke=1, fill=0)
    pdf.setLineWidth(1)
    pdf.roundRect(0.35 * inch, 0.35 * inch, width - 0.7 * inch, height - 0.7 * inch, 8, stroke=1, fill=0)

    # --- Header Section ---
    pdf.setFillColor(colors.HexColor("#061120"))
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawCentredString(width / 2, height - 1.0 * inch, "PRESTIGE INSTITUTE OF ENGINEERING MANAGEMENT & RESEARCH, INDORE")
    
    pdf.setFont("Helvetica-Bold", 10)
    pdf.setFillColor(colors.HexColor("#475569"))
    pdf.drawCentredString(width / 2, height - 1.2 * inch, "NBA ACCREDITED | APPROVED BY AICTE, NEW DELHI | AFFILIATED TO RGPV & DAVV")

    # --- URJOTSAV 2K26 LOGO Area ---
    pdf.setFillColor(colors.HexColor("#061120"))
    pdf.setFont("Helvetica-Bold", 38)
    pdf.drawCentredString(width / 2, height - 1.9 * inch, "URJOTSAV 2K26")
    
    pdf.setStrokeColor(colors.HexColor("#F97316"))
    pdf.setLineWidth(4)
    pdf.line(width/2 - 1.6*inch, height - 2.1*inch, width/2 + 1.6*inch, height - 2.1*inch)

    # --- Title Banner ---
    banner_y = height - 2.8 * inch
    pdf.setFillColor(colors.HexColor("#F97316"))
    pdf.rect(width/2 - 2.5*inch, banner_y, 5*inch, 0.45*inch, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(width / 2, banner_y + 0.12 * inch, "CERTIFICATE OF APPRECIATION")

    # --- Main Content ---
    pdf.setFillColor(colors.HexColor("#1E293B"))
    pdf.setFont("Helvetica", 16)
    pdf.drawCentredString(width / 2, height - 3.6 * inch, "This is to certify that")

    pdf.setFillColor(colors.HexColor("#061120"))
    pdf.setFont("Helvetica-Bold", 34)
    pdf.drawCentredString(width / 2, height - 4.2 * inch, registration.full_name)

    pdf.setFillColor(colors.HexColor("#475569"))
    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(width / 2, height - 4.75 * inch, f"has participated in the event '{event.title}'")
    pdf.drawCentredString(width / 2, height - 5.05 * inch, "organized as part of the Annual Technical, Cultural and Sports Festival Urjotsav 2K26.")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawCentredString(width / 2, height - 5.45 * inch, f"Held on {event.event_date} at {event.venue}")

    # --- DIGITAL SIGNATURE SECTION (Premium) ---
    sig_box_y = 1.0 * inch
    pdf.setStrokeColor(colors.HexColor("#E2E8F0"))
    pdf.setLineWidth(1)
    pdf.roundRect(width/2 - 1.5*inch, sig_box_y, 3*inch, 0.7*inch, 5, stroke=1, fill=0)
    
    pdf.setFillColor(colors.HexColor("#22C55E")) # Success Green
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawCentredString(width / 2, sig_box_y + 0.45 * inch, "DIGITALLY SIGNED & VERIFIED")
    
    pdf.setFillColor(colors.HexColor("#64748B"))
    pdf.setFont("Helvetica", 8)
    pdf.drawCentredString(width / 2, sig_box_y + 0.25 * inch, "Secured via PIEMR Digital Certification System")
    pdf.drawCentredString(width / 2, sig_box_y + 0.12 * inch, f"Timestamp: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')} IST")

    # --- Footer / ID ---
    pdf.setFillColor(colors.HexColor("#94A3B8"))
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawCentredString(width / 2, 0.65 * inch, f"Certificate ID: {cert_id}")
    
    pdf.setFont("Helvetica", 8)
    pdf.drawCentredString(width / 2, 0.48 * inch, "This is a computer-generated certificate and does not require a physical signature.")
    pdf.drawCentredString(width / 2, 0.35 * inch, "Verify authenticity at: seminar.pythonanywhere.com/certificate/")

    pdf.save()

    with output_path.open("rb") as handle:
        registration.certificate_pdf.save(output_path.name, File(handle), save=False)
    registration.save(update_fields=["certificate_id", "certificate_pdf", "updated_at"])


def send_certificate_email(registration):
    if not registration.certificate_pdf or not Path(registration.certificate_pdf.path).exists():
        generate_certificate(registration)

    subject = f"Certificate of Participation - Urjotsav 2K26"
    body = (
        f"Dear {registration.full_name},\n\n"
        f"Congratulations on your participation in Urjotsav 2K26 at PIEMR, Indore.\n"
        f"Your certificate ID is {registration.certificate_id}. This is a digitally verified certificate.\n\n"
        "Regards,\nUrjotsav 2K26 Team\nPIEMR, Indore"
    )
    email = EmailMessage(subject, body, to=[registration.email])
    certificate_path = Path(registration.certificate_pdf.path)
    email.attach_file(certificate_path)
    email.send(fail_silently=False)
    registration.certificate_emailed_at = timezone.now()
    registration.save(update_fields=["certificate_emailed_at", "updated_at"])
