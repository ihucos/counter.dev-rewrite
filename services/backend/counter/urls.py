from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework.routers import SimpleRouter
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from core import api

router = SimpleRouter(trailing_slash="")
router.register("sites", api.SiteViewSet, basename="sites")

urlpatterns = [
    # Authentication & account
    path("login", api.login_view, name="login"),
    path("logout", api.logout_view, name="logout"),
    path("register", api.register_view, name="register"),
    path("recover", api.recover_view, name="recover"),
    path("account_edit", api.account_edit_view, name="account_edit"),
    path("delete_user", api.delete_user_view, name="delete_user"),
    path("feedback", api.feedback_view, name="feedback"),
    # Sites
    path("delete_site", api.delete_site_view, name="delete_site"),
    # Guest / share access
    path("reset_token", api.reset_token_view, name="reset_token"),
    path("delete_token", api.delete_token_view, name="delete_token"),
    # Dashboard preferences
    path("set_pref_site", api.set_pref_site_view, name="set_pref_site"),
    path("set_pref_range", api.set_pref_range_view, name="set_pref_range"),
    # Dashboard data
    path("query", api.query_view, name="query"),
    path("me", api.me_view, name="me"),
    # Misc
    path("lang", api.lang_view, name="lang"),
    path("newsletter_register", api.newsletter_register_view, name="newsletter_register"),
    path("subscribed", api.subscribed_view, name="subscribed"),
    path("", include(router.urls)),
    # API documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("admin/", admin.site.urls),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)