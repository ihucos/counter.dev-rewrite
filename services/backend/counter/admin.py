from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "email",
        "uuid",
        "timezone",
        "hide_hosts",
        "is_staff",
    )
    list_filter = ("hide_hosts", "is_staff", "is_superuser")
    search_fields = ("username", "email", "uuid")
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Counter Profile",
            {
                "fields": (
                    "uuid",
                    "timezone",
                    "prefs",
                    "hide_hosts",
                )
            },
        ),
    )
