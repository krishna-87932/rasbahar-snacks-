from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.conf import settings as app_settings
from django.utils import timezone
import random
import string
import math


class UserManager(BaseUserManager):
    def create_user(self, phone_number, name, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('Phone number is required')
        email = extra_fields.get('email')
        if not email:
            raise ValueError('The Email field must be set')
        extra_fields['email'] = self.normalize_email(email)

        user = self.model(phone_number=phone_number, name=name, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(phone_number, name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    address = models.TextField(blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_active = models.BooleanField(default=False)  # Activated via OTP
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['name', 'email']

    objects = UserManager()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.name} ({self.phone_number})"

    @property
    def has_location(self):
        """Check if user has GPS coordinates saved."""
        return self.latitude is not None and self.longitude is not None

    @property
    def distance_from_restaurant_km(self):
        """Calculate distance from restaurant using Haversine formula. Returns km or None."""
        if not self.has_location:
            return None
        R = 6371  # Earth's radius in km
        lat1 = math.radians(app_settings.RESTAURANT_LAT)
        lat2 = math.radians(self.latitude)
        dlat = math.radians(self.latitude - app_settings.RESTAURANT_LAT)
        dlng = math.radians(self.longitude - app_settings.RESTAURANT_LNG)
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 2)

    @property
    def is_within_delivery_range(self):
        """Check if user is within the delivery radius."""
        dist = self.distance_from_restaurant_km
        if dist is None:
            return False
        return dist <= app_settings.MAX_DELIVERY_RADIUS_KM


def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))


class OTPRecord(models.Model):
    PURPOSE_REGISTER = 'register'
    PURPOSE_LOGIN = 'login'
    PURPOSE_RESET = 'reset'
    PURPOSE_CHOICES = [
        (PURPOSE_REGISTER, 'Registration'),
        (PURPOSE_LOGIN, 'Login'),
        (PURPOSE_RESET, 'Password Reset'),
    ]

    phone_number = models.CharField(max_length=15)
    otp = models.CharField(max_length=10)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP for {self.phone_number} [{self.purpose}]"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired

    @classmethod
    def create_otp(cls, phone_number, purpose, expiry_minutes=10):
        # Invalidate old OTPs for same phone + purpose
        cls.objects.filter(
            phone_number=phone_number,
            purpose=purpose,
            is_used=False
        ).update(is_used=True)

        otp = generate_otp()
        record = cls.objects.create(
            phone_number=phone_number,
            otp=otp,
            purpose=purpose,
            expires_at=timezone.now() + timezone.timedelta(minutes=expiry_minutes)
        )
        return record

    @classmethod
    def verify_otp(cls, phone_number, otp, purpose):
        try:
            record = cls.objects.filter(
                phone_number=phone_number,
                otp=otp,
                purpose=purpose,
                is_used=False
            ).latest('created_at')
            if record.is_expired:
                return None, 'OTP has expired.'
            record.is_used = True
            record.save()
            return record, None
        except cls.DoesNotExist:
            return None, 'Invalid OTP.'
