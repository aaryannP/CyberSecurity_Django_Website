from django.db import models

class CustomUser(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    password = models.CharField(max_length=256) # For hashed password
    is_verified = models.BooleanField(default=False)
    risk_level = models.CharField(max_length=20, default='Normal')
    created_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_blocked = models.BooleanField(default=False)
    blocked_until = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.email

class LoginLog(models.Model):
    email = models.EmailField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    login_time = models.DateTimeField(auto_now_add=True)
    is_suspicious = models.BooleanField(default=False)
    success = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.email} - {self.ip_address} - {'Success' if self.success else 'Failed'}"

class ActivityLog(models.Model):
    user_email = models.EmailField()
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_suspicious = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user_email} - {self.action}"

class OTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} - {self.otp}"
