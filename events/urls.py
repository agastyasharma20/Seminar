from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("payment/", views.payment_view, name="payment"),
    path("certificate/", views.certificate_lookup, name="certificate_lookup"),
    path("control-room/", views.admin_dashboard, name="admin_dashboard"),
    path("control-room/settings/", views.admin_settings, name="admin_settings"),
    path("control-room/registration/<int:pk>/<str:status>/", views.admin_update_registration, name="admin_update_registration"),
    path("control-room/registration/<int:pk>/email/", views.admin_email_certificate, name="admin_email_certificate"),
    path("control-room/export/", views.admin_export, name="admin_export"),
]
