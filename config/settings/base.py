"""
Writing Hub — Base Settings (ADR-083)

Package-Integration:
  - iil-aifw      → INSTALLED_APPS: "aifw"           (DB-driven LLM routing)
  - iil-weltenfw  → INSTALLED_APPS: "weltenfw.django" (WeltenHub REST client)
  - iil-promptfw  → kein INSTALLED_APPS (pure Python library)
  - iil-authoringfw → kein INSTALLED_APPS (pure Python schemas)

Settings:
  WELTENHUB_URL   = https://weltenforger.com/api/v1  (WeltenHub API endpoint)
  WELTENHUB_TOKEN = <token>                           (per-tenant API token)
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-writing-hub-dev-key")

DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # Third-party
    "rest_framework",
    "django_filters",
    "crispy_forms",
    "crispy_bootstrap5",
    # iil Platform packages (Django-integrated)
    "aifw",                  # LLM routing: AIActionType, LLMProvider, AIUsageLog
    "weltenfw.django",       # WeltenHub client: get_client() singleton
    # Local apps
    "apps.core.apps.CoreConfig",
    "apps.projects.apps.ProjectsConfig",
    "apps.series.apps.SeriesConfig",
    "apps.authoring.apps.AuthoringConfig",
    "apps.illustration.apps.IllustrationConfig",
    "apps.idea_import.apps.IdeaImportConfig",
    "apps.api.apps.ApiConfig",
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

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("DB_NAME", BASE_DIR / "db.sqlite3"),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", ""),
        "PORT": os.environ.get("DB_PORT", ""),
    }
}

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

# ============================================================================
# iil-weltenfw — WeltenHub REST Client
# Dokumentation: https://pypi.org/project/iil-weltenfw/
# get_client() liefert WeltenClient-Singleton pro Worker (lazy init).
# Multi-Tenant: eigenen WeltenClient(token=user_token) pro Request erstellen.
# ============================================================================
WELTENHUB_URL = os.environ.get("WELTENHUB_URL", "https://weltenforger.com/api/v1")
WELTENHUB_TOKEN = os.environ.get("WELTENHUB_TOKEN", "")
WELTENHUB_LOOKUP_TTL = int(os.environ.get("WELTENHUB_LOOKUP_TTL", "3600"))
WELTENHUB_TIMEOUT = float(os.environ.get("WELTENHUB_TIMEOUT", "30.0"))

# ============================================================================
# iil-aifw — LLM Routing
# Konfiguration via Django Admin: AIActionType, LLMProvider, LLMModel
# Seed: python manage.py init_llm_config
# action_codes für writing-hub:
#   chapter_write, chapter_brief, chapter_analyze
#   character_generate, outline_generate, outline_beat_expand
#   idea_generate, idea_to_premise, style_check
#   world_generate, world_expand, world_locations
# ============================================================================

# ============================================================================
# iil-promptfw — Prompt Templates
# YAML-Templates in templates/prompts/ ablegen.
# Laden: PromptStack.from_directory(BASE_DIR / "templates" / "prompts")
# ============================================================================
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

LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/"
