from django.contrib import admin

from .models import Count, Host


@admin.register(Host)
class HostAdmin(admin.ModelAdmin):
    list_display = ("name", "user")
    search_fields = ("name", "user__username")


@admin.register(Count)
class CountAdmin(admin.ModelAdmin):
    list_display = ("host", "date", "category", "item", "total")
    list_filter = ("category", "date")
    search_fields = ("host__name", "item")
