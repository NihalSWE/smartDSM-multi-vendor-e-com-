from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager, Group, Permission
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from .utils.slug_utils import generate_unique_slug
from django.utils import timezone
from django.core.files.storage import default_storage
from io import BytesIO
from django.core.files.base import ContentFile
from decimal import Decimal
import uuid





class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, user_id=None, user_type=3, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        if not username:
            raise ValueError("Username is required")
        if not password:
            raise ValueError("Password is required")

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            username=username,
            user_id=user_id or f"user_{uuid.uuid4().hex[:8]}",
            user_type=user_type,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, user_id=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 0)

        # Let create_user handle user_id generation
        return self.create_user(
            email=email,
            username=username,
            password=password,
            user_id=user_id,  # Can be None
            **extra_fields
        )


class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = (
        (0, 'Root'),
        (1, 'Vendor'),
        (2, 'Staff'),
        (3, 'Client'),
    )

    STATUS_CHOICES = (
        (0, 'Inactive'),
        (1, 'Active'),
        (2, 'Suspended'),
    )

    user_id = models.CharField(unique=True, max_length=15, blank=True, null=True)
    username = models.CharField(unique=True, max_length=150, blank=True, null=True)
    email = models.EmailField(unique=True, max_length=100)
    phone_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    address = models.CharField(max_length=250, blank=True, null=True)
    user_type = models.IntegerField(choices=USER_TYPE_CHOICES, default=2)
    user_status = models.IntegerField(choices=STATUS_CHOICES, default=1)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    # REQUIRED_FIELDS = ['user_id', 'username', 'phone_number']

    def __str__(self):
        return self.username


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    hire_date = models.DateField(null=True, blank=True)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    profile_picture = models.URLField(blank=True, null=True)
    linkedin_profile = models.URLField(blank=True, null=True)
    github_profile = models.URLField(blank=True, null=True)
    biography = models.TextField(blank=True, null=True)
    timezone = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.user.username
    
    