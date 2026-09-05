import os
from pathlib import Path


# Service hostnames: the compose services export POSTGRES_HOST/REDIS_HOST so
# containers reach each other by Docker DNS name, while the default
# "localhost" fits host-side runs (backend tests, local dev). Never fall back
# to "localhost" on a failed DNS probe inside a container — that silently
# pointed sync at its own loopback and crash-looped it.
BASE_DIR = Path(__file__).resolve().parent.parent

POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")

STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = "/var/www/example.com/static/"

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    # Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "markdownify.apps.MarkdownifyConfig",
    # Custom apps
    "rest_framework",
    "counter",
    "core",
]

MIDDLEWARE = [
    "core.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "counter.urls"

WSGI_APPLICATION = "counter.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "counter",
        "USER": "counter",
        "PASSWORD": "counter",
        "HOST": POSTGRES_HOST,
        "PORT": 5432,
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:6379/0",
    }
}

AUTH_USER_MODEL = "counter.User"

# The API is consumed by the SPA via fetch(); JSON only, no browsable API
# templates, and no pagination so the sites list is a plain array.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["core.authentication.AccountAuthentication"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "UNAUTHENTICATED_USER": "django.contrib.auth.models.AnonymousUser",
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# API endpoints are reached cross-origin (the SPA on counter.dev calls
# api.counter.dev directly), so core.middleware.CorsMiddleware grants the SPA
# origins access, with credentials so the session cookie flows. The API
# endpoints are CSRF-exempt and rely on the session cookie only. Locally the
# SPA runs on counterdev.test, which is same-site with api.counterdev.test
# (two-label base under a non-TLD), so the SameSite=Lax cookie just works.
CORS_ALLOWED_ORIGINS = os.environ.get(
    "DJANGO_CORS_ORIGINS",
    "https://counter.dev,https://www.counter.dev,http://counterdev.test",
).split(",")

# When behind the nginx reverse proxy, trust the X-Forwarded-Proto header

# When behind the nginx reverse proxy, trust the X-Forwarded-Proto header
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

EMAIL_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@counter.dev")
PASSWORD_RESET_URL_BASE = os.environ.get(
    "PASSWORD_RESET_URL_BASE", "https://counter.dev/reset"
)

MARKDOWNIFY = {
    "default": {
        "WHITELIST_TAGS": [
            "a",
            "p",
            "strong",
            "em",
            "u",
            "i",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",  # Added header tags
            "ul",
            "ol",
            "li",
            "blockquote",
            "code",
            "pre",
        ],
        "MARKDOWN_EXTENSIONS": [
            "markdown.extensions.fenced_code",
            "markdown.extensions.extra",
        ],
    }
}
