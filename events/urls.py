from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("app/", views.dashboard, name="dashboard"),
    path("app/scan/", views.scan_create, name="scan_create"),
    path("app/scans/", views.scan_history, name="scan_history"),
    path("app/scans/<int:scan_id>/", views.scan_review, name="scan_review"),
    path("app/contacts/", views.contact_list, name="contacts"),
    path("app/contacts/<int:contact_id>/", views.contact_detail, name="contact_detail"),
    path("app/contacts/<int:contact_id>/vcf/", views.vcf_download, name="vcf_download"),
    path("admin/", views.admin_dashboard, name="admin_dashboard"),
    path("admin/scans/", views.admin_scans, name="admin_scans"),
    path("admin/review/", views.admin_review, name="admin_review"),
    path("admin/audit/", views.admin_audit, name="admin_audit"),
    path("admin/export/", views.admin_export, name="admin_export"),
]
