import uuid
import secrets
import hashlib
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings

class UserRole(models.TextChoices):
    ADMINISTRATOR = 'administrator', 'Administrator'
    VIEWER = 'viewer', 'Viewer'

class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.ADMINISTRATOR,
        help_text="Role-based access: Administrator or Viewer"
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    organization = models.CharField(max_length=150, default="Sunscrap Recyclers PVT LTD")
    email_verified = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_admin(self):
        return self.role == UserRole.ADMINISTRATOR or self.is_superuser

    @property
    def is_viewer(self):
        return self.role == UserRole.VIEWER

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class EmailOTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='otp_requests')
    email = models.EmailField()
    code_hash = models.CharField(max_length=128)
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    @classmethod
    def create_otp(cls, user, email):
        raw_code = f"{secrets.randbelow(1000000):06d}"
        salt = settings.SECRET_KEY[:16]
        code_hash = hashlib.sha256(f"{raw_code}:{salt}".encode()).hexdigest()
        expires_at = timezone.now() + timedelta(seconds=getattr(settings, 'OTP_EXPIRY_SECONDS', 300))
        otp = cls.objects.create(
            user=user,
            email=email,
            code_hash=code_hash,
            expires_at=expires_at
        )
        return otp, raw_code

    def verify(self, raw_code):
        if self.is_used:
            return False, "OTP has already been used."
        if timezone.now() > self.expires_at:
            return False, "OTP has expired."
        if self.attempts >= self.max_attempts:
            return False, "Maximum attempts reached. Please request a new OTP."
        
        self.attempts += 1
        salt = settings.SECRET_KEY[:16]
        check_hash = hashlib.sha256(f"{raw_code}:{salt}".encode()).hexdigest()
        if check_hash == self.code_hash:
            self.is_used = True
            self.save(update_fields=['attempts', 'is_used'])
            return True, "Verification successful."
        
        self.save(update_fields=['attempts'])
        remaining = self.max_attempts - self.attempts
        return False, f"Invalid OTP code. {remaining} attempt(s) remaining."


class PasswordResetToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='password_resets')
    token = models.CharField(max_length=64, unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    @classmethod
    def create_token(cls, user):
        expires_at = timezone.now() + timedelta(hours=2)
        return cls.objects.create(user=user, token=secrets.token_urlsafe(32), expires_at=expires_at)

    def is_valid(self):
        return not self.is_used and timezone.now() <= self.expires_at


class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp}] {self.user} - {self.action}"
