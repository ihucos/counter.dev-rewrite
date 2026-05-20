from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"hosts", views.HostViewSet, basename="host")

urlpatterns = [
    path("", include(router.urls)),
    path("ingress/", views.ingress, name="ingress"),
    path("query/", views.query, name="query"),
]
