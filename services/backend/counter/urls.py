from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from . import views

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("", views.index, name="index"),
    path("privacy", views.privacy, name="privacy"),
    path("admin/", admin.site.urls),
    path("api/core/", include("core.urls")),
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
