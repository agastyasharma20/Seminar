import csv

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EventSettingsForm, LoginForm, PaymentForm, ProfileForm, SignupForm
from .models import Registration
from .utils import generate_certificate, get_event_settings, send_certificate_email


def is_staff(user):
    return user.is_authenticated and user.is_staff


def home(request):
    event = get_event_settings()
    return render(request, "events/home.html", {"event": event})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Account created. Complete your participant profile to continue.")
        return redirect("dashboard")
    return render(request, "events/auth.html", {"form": form, "mode": "signup"})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.cleaned_data["user"])
        return redirect("admin_dashboard" if form.cleaned_data["user"].is_staff else "dashboard")
    return render(request, "events/auth.html", {"form": form, "mode": "login"})


def logout_view(request):
    logout(request)
    messages.success(request, "You are signed out.")
    return redirect("home")


@login_required
def dashboard(request):
    if request.user.is_staff:
        return redirect("admin_dashboard")

    event = get_event_settings()
    registration, created = Registration.objects.get_or_create(
        user=request.user,
        defaults={
            "event": event,
            "full_name": request.user.get_full_name() or request.user.username,
            "participant_type": Registration.ParticipantType.STUDENT,
            "phone": None,
        },
    )
    if registration.event_id != event.id:
        registration.event = event
        registration.save(update_fields=["event", "updated_at"])

    initial = registration.profile_data or {}
    form = ProfileForm(request.POST or None, instance=registration, initial=initial)
    if request.method == "POST" and form.is_valid():
        registration = form.save(commit=False)
        registration.event = event
        if registration.status == Registration.Status.DRAFT:
            registration.status = Registration.Status.PAYMENT_PENDING
        registration.save()
        messages.success(request, "Profile saved. Continue with payment.")
        return redirect("payment")

    return render(request, "events/dashboard.html", {"event": event, "registration": registration, "form": form})


@login_required
def payment_view(request):
    if request.user.is_staff:
        return redirect("admin_dashboard")
    event = get_event_settings()
    if not event.registration_open:
        messages.warning(request, "Registrations are currently closed by the admin.")
        return redirect("dashboard")

    registration = get_object_or_404(Registration, user=request.user)
    if not registration.phone:
        messages.warning(request, "Please complete your participant profile before payment.")
        return redirect("dashboard")
    if event.approved_count >= event.seat_limit and registration.status != Registration.Status.APPROVED:
        messages.warning(request, "All seats are currently filled.")
        return redirect("dashboard")

    form = PaymentForm(request.POST or None, request.FILES or None, instance=registration)
    if request.method == "POST" and form.is_valid():
        registration = form.save(commit=False)
        registration.status = Registration.Status.PENDING
        registration.save()
        messages.success(request, "Payment details submitted. Admin verification is pending.")
        return redirect("dashboard")
    return render(request, "events/payment.html", {"event": event, "registration": registration, "form": form})


def certificate_lookup(request):
    result = None
    email = ""
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        user = User.objects.filter(email=email).first()
        result = getattr(user, "registration", None) if user else None
        if not result:
            messages.warning(request, "No registration found for this email.")
    return render(request, "events/certificate_lookup.html", {"result": result, "email": email})


@user_passes_test(is_staff, login_url="login")
def admin_dashboard(request):
    event = get_event_settings()
    rows = Registration.objects.select_related("user", "event").order_by("-created_at")
    counts = {choice.value: rows.filter(status=choice.value).count() for choice in Registration.Status}
    return render(request, "events/admin_dashboard.html", {"event": event, "rows": rows, "counts": counts})


@user_passes_test(is_staff, login_url="login")
def admin_settings(request):
    event = get_event_settings()
    form = EventSettingsForm(request.POST or None, request.FILES or None, instance=event)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Event settings updated.")
        return redirect("admin_dashboard")
    messages.error(request, "Please fix the highlighted event settings.")
    return redirect("admin_dashboard")


@user_passes_test(is_staff, login_url="login")
def admin_update_registration(request, pk, status):
    registration = get_object_or_404(Registration.objects.select_related("event", "user"), pk=pk)
    valid_statuses = {choice.value for choice in Registration.Status}
    if status not in valid_statuses:
        messages.error(request, "Invalid status.")
        return redirect("admin_dashboard")
    if status == Registration.Status.APPROVED and registration.event.approved_count >= registration.event.seat_limit and registration.status != Registration.Status.APPROVED:
        messages.error(request, "Seat limit reached. Increase seats before approving more participants.")
        return redirect("admin_dashboard")

    registration.status = status
    registration.admin_note = request.POST.get("admin_note", "")
    if status == Registration.Status.APPROVED and not registration.certificate_pdf:
        generate_certificate(registration)
    registration.save()
    messages.success(request, f"{registration.full_name} marked as {registration.get_status_display()}.")
    return redirect("admin_dashboard")


@user_passes_test(is_staff, login_url="login")
def admin_email_certificate(request, pk):
    registration = get_object_or_404(Registration.objects.select_related("event", "user"), pk=pk)
    if registration.status != Registration.Status.APPROVED:
        messages.error(request, "Approve the registration before emailing a certificate.")
        return redirect("admin_dashboard")
    try:
        send_certificate_email(registration)
        messages.success(request, f"Certificate emailed to {registration.email}.")
    except Exception as exc:
        messages.error(request, f"Email failed: {exc}")
    return redirect("admin_dashboard")


@user_passes_test(is_staff, login_url="login")
def admin_export(request):
    rows = Registration.objects.select_related("user", "event").order_by("-created_at")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="piemr-seminar-registrations.csv"'
    writer = csv.writer(response)
    writer.writerow(["Name", "Email", "Phone", "Type", "City", "Profile Data", "Transaction ID", "Status", "Certificate ID", "Emailed At"])
    for row in rows:
        writer.writerow([
            row.full_name,
            row.email,
            row.phone,
            row.get_participant_type_display(),
            row.city,
            row.profile_data,
            row.transaction_id,
            row.get_status_display(),
            row.certificate_id,
            row.certificate_emailed_at,
        ])
    return response
