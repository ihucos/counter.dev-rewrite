from django.urls import include, path

from core import views

urlpatterns = [
    path("query/", views.query, name="query"),
    path("logs/", views.visit_logs, name="visit-logs"),
]
