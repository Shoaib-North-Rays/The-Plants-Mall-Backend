from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import *


@admin.register(User)
class UserAdmin(BaseUserAdmin):
     
    list_display = ("username", "email", "name", "role", "is_active", "is_staff" )
    list_filter = ("role", "is_active", "is_staff")

     
    fieldsets = (
        (None, {"fields": ("username", "email", "name", "phone", "password","profile_pic")}),
        (_("Permissions"), {"fields": ("role", "is_active", "is_staff", "groups", "user_permissions")}),
    )

     
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "name", "phone", "role", "password1", "password2","profile_pic"),
        }),
    )

    search_fields = ("username", "email", "name")
    ordering = ("username",)
 