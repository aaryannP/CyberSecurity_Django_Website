from django.urls import path
from . import views

urlpatterns = [
    path('register', views.register_view, name='register'),
    path('verify/', views.verify_otp_view, name='verify_otp'),
    path('otp-verify/', views.verify_otp_view, name='otp_verify'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
    path('verify-reset-otp/', views.verify_reset_otp_view, name='verify_reset_otp'),
    path('suspicious-activity/', views.suspicious_activity_view, name='suspicious_activity'),
    path('login-attempts/', views.login_attempts_view, name='login_attempts'),
    path('risk-analysis/', views.risk_analysis_view, name='risk_analysis'),
    path('alerts/', views.alerts_view, name='alerts'),
    path('users/', views.users_view, name='users'),
    path('reports/', views.reports_view, name='reports'),
]
