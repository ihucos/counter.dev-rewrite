from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"hosts", views.HostViewSet, basename="host")

urlpatterns = [
    path("", include(router.urls)),
    path("query/", views.query, name="query"),
    path("logs/", views.visit_logs, name="visit-logs"),
]
