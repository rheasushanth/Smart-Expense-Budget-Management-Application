
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "Administrator")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("A superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("A superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = "Customer", "Customer"
        ADMINISTRATOR = "Administrator", "Administrator"

    user_id = models.BigAutoField(primary_key=True)
    username = None

    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
    )

    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    failed_login_window_started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    def __str__(self):
        return self.email


class SecurityEvent(models.Model):
    class EventType(models.TextChoices):
        FAILED_LOGIN = "FAILED_LOGIN", "Failed Login"
        ACCOUNT_LOCKED = "ACCOUNT_LOCKED", "Account Locked"
        UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS", "Unauthorized Access"
        CATEGORY_CREATED = "CATEGORY_CREATED", "Category Created"
        CATEGORY_UPDATED = "CATEGORY_UPDATED", "Category Updated"
        CATEGORY_STATUS_CHANGED = (
            "CATEGORY_STATUS_CHANGED",
            "Category Status Changed",
        )

    event_type = models.CharField(max_length=40, choices=EventType.choices)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="security_events",
    )

    email = models.EmailField(blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.event_type} - {self.timestamp}"
