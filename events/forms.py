from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from .models import EventSettings, Registration


class SignupForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") != cleaned.get("confirm_password"):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned

    def save(self):
        return User.objects.create_user(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password"],
        )


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        user = authenticate(username=cleaned.get("username"), password=cleaned.get("password"))
        if not user:
            raise forms.ValidationError("Invalid username or password.")
        cleaned["user"] = user
        return cleaned


class ProfileForm(forms.ModelForm):
    institution = forms.CharField(required=False, label="Institution / University")
    course = forms.CharField(required=False)
    branch = forms.CharField(required=False)
    year = forms.CharField(required=False)
    department = forms.CharField(required=False)
    designation = forms.CharField(required=False)
    research_area = forms.CharField(required=False)
    company = forms.CharField(required=False)
    experience = forms.CharField(required=False, label="Experience")

    class Meta:
        model = Registration
        fields = ["full_name", "phone", "participant_type", "city"]

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        if not phone:
            raise forms.ValidationError("Phone number is required.")
        qs = Registration.objects.filter(phone=phone)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This phone number is already registered.")
        return phone

    def clean(self):
        cleaned = super().clean()
        participant_type = cleaned.get("participant_type")
        required_by_type = {
            Registration.ParticipantType.STUDENT: ["institution", "course", "branch", "year"],
            Registration.ParticipantType.FACULTY: ["institution", "department", "designation"],
            Registration.ParticipantType.RESEARCHER: ["institution", "research_area"],
            Registration.ParticipantType.INDUSTRY: ["company", "designation", "experience"],
        }
        for field in required_by_type.get(participant_type, []):
            if not cleaned.get(field):
                self.add_error(field, "Required for this participant type.")
        return cleaned

    def save(self, commit=True):
        registration = super().save(commit=False)
        fields = ["institution", "course", "branch", "year", "department", "designation", "research_area", "company", "experience"]
        registration.profile_data = {field: self.cleaned_data.get(field, "") for field in fields if self.cleaned_data.get(field)}
        if commit:
            registration.save()
        return registration


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ["transaction_id", "payment_screenshot"]


class EventSettingsForm(forms.ModelForm):
    class Meta:
        model = EventSettings
        fields = [
            "title",
            "organizer",
            "organized_by",
            "event_scope",
            "expert_name",
            "expert_title",
            "expert_linkedin",
            "expert_image_url",
            "event_date",
            "event_time",
            "venue",
            "fee",
            "seat_limit",
            "registration_open",
            "qr_code",
            "upi_note",
            "faculty_coordinator_name",
            "faculty_coordinator_detail",
            "faculty_coordinator_email",
            "student_coordinator_name",
            "student_coordinator_detail",
            "student_coordinator_email",
            "volunteer_details",
            "developer_linkedin",
        ]
