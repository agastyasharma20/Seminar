import csv
from datetime import timedelta

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import LoginForm, SignupForm
from .models import AuditLog, Contact, Scan


def is_staff(user):
    return user.is_authenticated and user.is_staff


def record(actor, action, resource, resource_id=""):
    AuditLog.objects.create(actor=actor if getattr(actor, "is_authenticated", False) else None, action=action, resource=resource, resource_id=str(resource_id))


def demo_payload():
    return {"full_name": "Rahul Sharma", "job_title": "Senior Product Manager", "company": "Aster Labs", "email": "rahul.sharma@asterlabs.in", "phone": "+91 98765 43210", "website": "https://asterlabs.in", "linkedin": "https://linkedin.com/in/rahulsharma", "address": "Indiranagar, Bengaluru, Karnataka 560038", "industry": "Technology", "tags": ["Product", "Potential partner", "Bengaluru"]}


def home(request):
    return render(request, "events/home.html")


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(); login(request, user); record(user, "Account created", "user", user.id)
        return redirect("dashboard")
    return render(request, "events/auth.html", {"form": form, "mode": "signup"})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("admin_dashboard" if request.user.is_staff else "dashboard")
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.cleaned_data["user"]; login(request, user); record(user, "Login", "session")
        return redirect("admin_dashboard" if user.is_staff else "dashboard")
    return render(request, "events/auth.html", {"form": form, "mode": "login"})


def logout_view(request):
    if request.user.is_authenticated: record(request.user, "Logout", "session")
    logout(request)
    return redirect("home")


@login_required
def dashboard(request):
    if request.user.is_staff: return redirect("admin_dashboard")
    scans = Scan.objects.filter(user=request.user).select_related("contact")
    contacts = Contact.objects.filter(user=request.user)
    week = timezone.now() - timedelta(days=7)
    return render(request, "events/dashboard.html", {"contacts": contacts[:6], "scans": scans[:5], "stats": {"contacts": contacts.count(), "scans": scans.count(), "week": scans.filter(created_at__gte=week).count(), "companies": contacts.exclude(company="").values("company").distinct().count()}})


@login_required
def scan_create(request):
    if request.user.is_staff: return redirect("admin_dashboard")
    if request.method == "POST":
        data = demo_payload(); existing = Contact.objects.filter(user=request.user, email=data["email"]).first(); contact = existing or Contact.objects.create(user=request.user, **data)
        confidence = {"Name": 0.98, "Company": 0.94, "Job title": 0.87, "Email": 0.99, "Phone": 0.96, "Address": 0.71}
        scan = Scan.objects.create(user=request.user, contact=contact, scan_code=f"SCN-{timezone.now():%y%m%d%H%M%S}", original_name=request.FILES.get("card").name if request.FILES.get("card") else "demo-aster-labs-card.png", original_image=request.FILES.get("card"), raw_text="Rahul Sharma\nSenior Product Manager\nAster Labs\nrahul.sharma@asterlabs.in\n+91 98765 43210\nasterlabs.in", structured_data=data, validation_result={"email": "valid", "phone": "normalized", "website": "normalized"}, qr_data={"url": "https://asterlabs.in", "status": "Detected"}, field_confidence=confidence, ocr_confidence=0.94, extraction_confidence=0.91, duplicate_status="Possible duplicate" if existing else "No duplicate", processing_ms=2840, status=Scan.Status.REVIEW if existing else Scan.Status.COMPLETE)
        record(request.user, "Scan created", "scan", scan.scan_code); record(request.user, "Contact created" if not existing else "Duplicate detected", "contact", contact.id)
        return redirect("scan_review", scan_id=scan.id)
    return render(request, "events/scanner.html")


@login_required
def scan_review(request, scan_id):
    scan = get_object_or_404(Scan.objects.select_related("contact"), pk=scan_id)
    if not request.user.is_staff and scan.user_id != request.user.id: return HttpResponseForbidden("You cannot access this scan.")
    return render(request, "events/review.html", {"scan": scan, "contact": scan.contact, "confidence": scan.field_confidence.items()})


@login_required
def contact_list(request):
    from django.db.models import Q
    query = request.GET.get("q", "").strip(); contacts = Contact.objects.filter(user=request.user)
    if query: contacts = contacts.filter(Q(full_name__icontains=query) | Q(company__icontains=query) | Q(email__icontains=query) | Q(phone__icontains=query) | Q(job_title__icontains=query))
    return render(request, "events/contacts.html", {"contacts": contacts, "query": query})


@login_required
def contact_detail(request, contact_id):
    contact = get_object_or_404(Contact, pk=contact_id, user=request.user)
    return render(request, "events/contact_detail.html", {"contact": contact, "scans": contact.scans.all()})


@login_required
def vcf_download(request, contact_id):
    contact = get_object_or_404(Contact, pk=contact_id, user=request.user)
    lines = ["BEGIN:VCARD", "VERSION:3.0", f"FN:{contact.full_name}", f"ORG:{contact.company}", f"TITLE:{contact.job_title}"]
    if contact.phone: lines.append(f"TEL:{contact.phone}")
    if contact.email: lines.append(f"EMAIL:{contact.email}")
    if contact.website: lines.append(f"URL:{contact.website}")
    lines.append("END:VCARD"); record(request.user, "VCF generated", "contact", contact.id)
    response = HttpResponse("\r\n".join(lines), content_type="text/vcard"); response["Content-Disposition"] = f'attachment; filename="{contact.full_name.lower().replace(" ", "-")}.vcf"'
    return response


@login_required
def scan_history(request):
    return render(request, "events/history.html", {"scans": Scan.objects.filter(user=request.user).select_related("contact")})


@user_passes_test(is_staff, login_url="login")
def admin_dashboard(request):
    scans = Scan.objects.select_related("user", "contact")
    return render(request, "events/admin_dashboard.html", {"scans": scans[:8], "stats": {"scans": scans.count(), "users": User.objects.filter(is_staff=False).count(), "contacts": Contact.objects.count(), "success": scans.filter(status=Scan.Status.COMPLETE).count(), "review": scans.filter(status=Scan.Status.REVIEW).count()}})


@user_passes_test(is_staff, login_url="login")
def admin_scans(request): return render(request, "events/admin_scans.html", {"scans": Scan.objects.select_related("user", "contact")})


@user_passes_test(is_staff, login_url="login")
def admin_review(request): return render(request, "events/admin_review.html", {"scans": Scan.objects.select_related("user", "contact").filter(status=Scan.Status.REVIEW)})


@user_passes_test(is_staff, login_url="login")
def admin_audit(request): return render(request, "events/admin_audit.html", {"logs": AuditLog.objects.select_related("actor")[:60]})


@user_passes_test(is_staff, login_url="login")
def admin_export(request):
    response = HttpResponse(content_type="text/csv"); response["Content-Disposition"] = 'attachment; filename="cardiq-scans.csv"'
    writer = csv.writer(response); writer.writerow(["Scan ID", "User", "Status", "Contact", "OCR confidence", "Extraction confidence", "Created"])
    for scan in Scan.objects.select_related("user", "contact"): writer.writerow([scan.scan_code, scan.user.email, scan.get_status_display(), scan.contact, scan.ocr_confidence, scan.extraction_confidence, scan.created_at])
    record(request.user, "Admin exported data", "scans")
    return response
