from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core import views

urlpatterns = [
    # Pages
    path("", views.index, name="index"),
    path("privacy", views.privacy, name="privacy"),
    path("admin/", admin.site.urls),
    # Dashboard data
    path("dump", views.dump_sse, name="dump"),
    path("query", views.daterange_query, name="daterange-query"),
    path("api/core/", include("core.urls")),
    # Authentication & account
    path("login", views.login_view, name="login"),
    path("register", views.register_view, name="register"),
    path("recover", views.recover_view, name="recover"),
    path("account_edit", views.account_edit, name="account-edit"),
    path("delete_user", views.delete_user, name="delete-user"),
    path("feedback", views.feedback_view, name="feedback"),
    # Sites
    path("delete_site", views.delete_site, name="delete-site"),
    # Guest / share access
    path("reset_token", views.reset_token, name="reset-token"),
    path("delete_token", views.delete_token, name="delete-token"),
    # Dashboard preferences
    path("set_pref_site", views.set_pref_site, name="set-pref-site"),
    path("set_pref_range", views.set_pref_range, name="set-pref-range"),
    # Misc
    path("lang", views.lang, name="lang"),
    path("newsletter_register", views.newsletter_register, name="newsletter-register"),
    path("subscribed", views.subscribed, name="subscribed"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
