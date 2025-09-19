
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
import random
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta

class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("The Username is required")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(username, password, **extra_fields)




class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ("sales_man", "Sales Men"),
        ("admin", "Admin"),
        ("dispatcher", "Dispatcher"),
        ("delivery_rider", "Delivery Rider"),
    )

    username = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="sales_man")
    profile_pic=models.ImageField(upload_to="profiles", blank=True, null=True)
    last_activity = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "name"]

     
    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_set",   
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_set",   
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )
    @property
    def is_online(self):
        if self.last_activity:
            return timezone.now() - self.last_activity < timedelta(minutes=5)
        return False

    def __str__(self):
        return f"{self.username} ({self.role})"


User = get_user_model()

class VerificationCode(models.Model):
    CODE_FOR=(
        ("registration", "Registration"),
        ("password_reset", "Password Reset"),
    )
    user = models.ForeignKey(User, related_name="auth_codes", on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    use_for=models.CharField(choices=CODE_FOR,default="registration",max_length=100)
    expires_at = models.DateTimeField(default=timezone.now() + timezone.timedelta(minutes=10))
    def __str__(self):
        return f"{self.user.username} - {self.code}"
