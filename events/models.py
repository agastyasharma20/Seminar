from django.conf import settings
from django.db import models
from django.utils import timezone


class EventSettings(models.Model):
    title = models.CharField(max_length=220, default="Urjotsav 2K26 - Annual Fest")
    organizer = models.CharField(max_length=220, default="Prestige Institute of Engineering Management and Research, Indore")
    organized_by = models.CharField(
        max_length=220,
        default="PIEMR Student Council & Cultural Committee",
    )
    event_scope = models.CharField(max_length=80, default="National Event")
    expert_name = models.CharField(max_length=120, default="Mr. Dhawal Shrivastava")
    expert_title = models.CharField(
        max_length=220,
        default="Senior Security Assurance Engineering Lead, Microsoft Bangalore, India",
    )
    expert_linkedin = models.URLField(
        blank=True,
        default="https://www.linkedin.com/in/dhawalshrivastava/",
    )
    expert_image_url = models.URLField(
        blank=True,
        default="https://media.licdn.com/dms/image/v2/D4D03AQEHp61h7Scm_Q/profile-displayphoto-scale_400_400/B4DZ1mJcS7KUAg-/0/1775535249227?e=1778716800&v=beta&t=Tw6w9QjbI7f_BpVxEfIH-vUi52lW60lmLgn2AI5FrFw",
    )
    event_date = models.CharField(max_length=80, default="13 May 2026")
    event_time = models.CharField(max_length=80, default="10:00 AM - 3:00 PM")
    venue = models.TextField(
        default="Civil Auditorium, PIEMR, Prestige Vihar, Scheme Number 72, Vijay Nagar, Indore"
    )
    fee = models.PositiveIntegerField(default=100)
    seat_limit = models.PositiveIntegerField(default=100)
    registration_open = models.BooleanField(default=True)
    qr_code = models.ImageField(upload_to="qr/", blank=True, null=True)
    upi_note = models.CharField(max_length=180, default="Scan the UPI QR code uploaded by admin")
    faculty_coordinator_name = models.CharField(max_length=140, default="Prof Dr. Dinesh C Jain")
    faculty_coordinator_detail = models.CharField(max_length=180, default="Dept. of CSE")
    faculty_coordinator_email = models.EmailField(default="djain@piemr.edu.in")
    student_coordinator_name = models.CharField(max_length=140, default="Mr. Agastya Sharma")
    student_coordinator_detail = models.CharField(max_length=180, default="4 Sem CSE, PIEMR")
    student_coordinator_email = models.EmailField(default="51110105688@piemr.edu.in")
    volunteer_details = models.TextField(
        blank=True,
        help_text="Add one volunteer per line. Example: Name | Role/Class | email@example.com",
    )
    developer_linkedin = models.URLField(blank=True, help_text="Agastya Sharma LinkedIn profile URL for the footer credit.")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Event settings"

    def __str__(self):
        return self.title

    @property
    def approved_count(self):
        return self.registrations.filter(status=Registration.Status.APPROVED).count()

    @property
    def pending_count(self):
        return self.registrations.filter(status=Registration.Status.PENDING).count()

    @property
    def seats_left(self):
        return max(self.seat_limit - self.approved_count, 0)


class Registration(models.Model):
    class ParticipantType(models.TextChoices):
        STUDENT = "student", "Student"
        FACULTY = "faculty", "Faculty"
        RESEARCHER = "researcher", "Researcher"
        INDUSTRY = "industry", "Industry Professional"

    class Status(models.TextChoices):
        DRAFT = "draft", "Profile Pending"
        PAYMENT_PENDING = "payment_pending", "Payment Pending"
        PENDING = "pending", "Awaiting Admin Approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="registration")
    event = models.ForeignKey(EventSettings, on_delete=models.CASCADE, related_name="registrations")
    full_name = models.CharField(max_length=140)
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    participant_type = models.CharField(max_length=20, choices=ParticipantType.choices)
    city = models.CharField(max_length=80, blank=True)
    profile_data = models.JSONField(default=dict, blank=True)
    transaction_id = models.CharField(max_length=120, blank=True)
    payment_screenshot = models.FileField(upload_to="payments/", blank=True, null=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.DRAFT)
    certificate_id = models.CharField(max_length=40, unique=True, blank=True, null=True)
    certificate_pdf = models.FileField(upload_to="certificates/", blank=True, null=True)
    admin_note = models.TextField(blank=True)
    certificate_emailed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} - {self.get_status_display()}"

    @property
    def email(self):
        return self.user.email

    def mark_certificate_emailed(self):
        self.certificate_emailed_at = timezone.now()
        self.save(update_fields=["certificate_emailed_at", "updated_at"])
