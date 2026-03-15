"""
Writing Hub — Base Settings (ADR-083)
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-writing-hub-dev-key")

DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "rest_framework",
    "django_filters",
    "crispy_forms",
    "crispy_bootstrap5",
    "aifw",
    "weltenfw.django",
    "apps.core.apps.CoreConfig",
    "apps.worlds.apps.WorldsConfig",
    "apps.projects.apps.ProjectsConfig",
    "apps.series.apps.SeriesConfig",
    "apps.authoring.apps.AuthoringConfig",
    "apps.outlines.apps.OutlinesConfig",
    "apps.illustration.apps.IllustrationConfig",
    "apps.idea_import.apps.IdeaImportConfig",
    "apps.api.apps.ApiConfig",
    "apps.authors.apps.AuthorsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "config.wsgi.application"

# ADR-141: PostgreSQL default (no SQLite fallback)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "writing_hub"),
        "USER": os.environ.get("DB_USER", "dehnert"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5434"),
    }
}


AUTHENTICATION_BACKENDS = [
    "apps.accounts.auth.IILOIDCAuthenticationBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

FORMS_URLFIELD_ASSUME_HTTPS = True

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

WELTENHUB_URL = os.environ.get("WELTENHUB_URL", "https://weltenforger.com/api/v1")
WELTENHUB_TOKEN = os.environ.get("WELTENHUB_TOKEN", "")
WELTENHUB_LOOKUP_TTL = int(os.environ.get("WELTENHUB_LOOKUP_TTL", "3600"))
WELTENHUB_TIMEOUT = float(os.environ.get("WELTENHUB_TIMEOUT", "30.0"))

PROMPT_TEMPLATES_DIR = str(BASE_DIR / "templates" / "prompts")

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"},
        "simple": {"format": "{levelname} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "apps": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
        "weltenfw": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "aifw": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "SAMEORIGIN"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/projects/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

ADMIN_MEDIA_PREFIX = "/static/admin/"

# --- authentik OIDC (ADR-142) ---
OIDC_RP_CLIENT_ID = os.environ.get("OIDC_RP_CLIENT_ID", "")
OIDC_RP_CLIENT_SECRET = os.environ.get("OIDC_RP_CLIENT_SECRET", "")
_OIDC_APP_SLUG = os.environ.get("OIDC_APP_SLUG", "writing-hub")
_IDP = "https://id.iil.pet/application/o"
OIDC_OP_AUTHORIZATION_ENDPOINT = f"{_IDP}/authorize/"
OIDC_OP_TOKEN_ENDPOINT = f"{_IDP}/token/"
OIDC_OP_USER_ENDPOINT = f"{_IDP}/userinfo/"
OIDC_OP_JWKS_ENDPOINT = f"{_IDP}/{_OIDC_APP_SLUG}/jwks/"
OIDC_RP_SIGN_ALGO = "RS256"
OIDC_RP_SCOPES = "openid email profile"
LOGOUT_REDIRECT_URL = "/"
