from django.contrib import admin

from .models import EventSettings, Registration


@admin.register(EventSettings)
class EventSettingsAdmin(admin.ModelAdmin):
    list_display = ("title", "fee", "seat_limit", "registration_open", "updated_at")


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "participant_type", "status", "certificate_id", "created_at")
    list_filter = ("status", "participant_type", "created_at")
    search_fields = ("full_name", "user__email", "phone", "transaction_id", "certificate_id")
    readonly_fields = ("certificate_id", "certificate_emailed_at", "created_at", "updated_at")
