from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from core import api
from core import views as api_views
from . import views

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
    path("sites", api.SiteViewSet.as_view({"get": "list"}), name="sites"),
    path("sites/<str:site>", api.SiteViewSet.as_view({"get": "retrieve"}), name="site_detail"),
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
    # Pages
    path("", views.index, name="index"),
    path("privacy", views.privacy, name="privacy"),
    path("admin/", admin.site.urls),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)