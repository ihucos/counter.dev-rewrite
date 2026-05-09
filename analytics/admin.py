from django.contrib import admin

from .models import Count, Site


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("domain", "user", "filter_allowed_domains")
    search_fields = ("domain", "user__username")


@admin.register(Count)
class CountAdmin(admin.ModelAdmin):
    list_display = ("site", "date", "metric", "value", "count")
    list_filter = ("metric", "date")
    search_fields = ("site__domain", "value")
