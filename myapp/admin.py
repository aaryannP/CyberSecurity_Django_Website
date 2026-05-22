from django.contrib import admin
from .models import CustomUser, OTP, LoginLog, ActivityLog

# Register your models here.

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_verified', 'risk_level', 'created_ip', 'created_at')
    list_filter = ('is_verified', 'risk_level', 'created_at')
    search_fields = ('email',)
    ordering = ('-created_at',)

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('email', 'otp', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('email',)
    ordering = ('-created_at',)

@admin.register(LoginLog)
class LoginLogAdmin(admin.ModelAdmin):
    list_display = ('email', 'ip_address', 'login_time', 'success', 'is_suspicious')
    list_filter = ('success', 'is_suspicious', 'login_time')
    search_fields = ('email', 'ip_address')
    ordering = ('-login_time',)

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'action', 'timestamp', 'is_suspicious')
    list_filter = ('is_suspicious', 'timestamp', 'action')
    search_fields = ('user_email', 'action')
    ordering = ('-timestamp',)
