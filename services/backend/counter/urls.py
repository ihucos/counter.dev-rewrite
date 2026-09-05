from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework.routers import DynamicRoute, Route, SimpleRouter
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from core import api

router = SimpleRouter(trailing_slash="")


# A singleton resource has no detail routes: PUT/DELETE act on the collection
# itself (/account has no pk).
class SingletonRouter(SimpleRouter):
    routes = [
        Route(
            url=r"^{prefix}{trailing_slash}$",
            mapping={"get": "list", "put": "update", "delete": "destroy"},
            name="{basename}",
            detail=False,
            initkwargs={"suffix": "Instance"},
        ),
        # @action(detail=False) subresources, e.g. /account/share_token.
        DynamicRoute(
            url=r"^{prefix}/{url_path}{trailing_slash}$",
            name="{basename}_{url_name}",
            detail=False,
            initkwargs={},
        ),
    ]


account_router = SingletonRouter(trailing_slash="")
account_router.register("account", api.AccountViewSet, basename="account")
router.register("sites", api.SiteViewSet, basename="sites")

urlpatterns = [
    # Authentication & account
    path("login", api.login_view, name="login"),
    path("logout", api.logout_view, name="logout"),
    path("register", api.register_view, name="register"),
    path("recover", api.recover_view, name="recover"),
    path("feedback", api.feedback_view, name="feedback"),
    # Dashboard data
    path("query", api.query_view, name="query"),
    # Misc
    path("lang", api.lang_view, name="lang"),
    path("newsletter_register", api.newsletter_register_view, name="newsletter_register"),
    path("subscribed", api.subscribed_view, name="subscribed"),
    path("", include(router.urls)),
    path("", include(account_router.urls)),
    # API documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("admin/", admin.site.urls),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)