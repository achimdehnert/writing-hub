"""
Writing Hub — Production Settings
"""

from .base import *  # noqa: F401, F403
from decouple import config

DEBUG = False

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="writing.iil.pet").split(",")
# ADR-021: Internal hosts for Docker/LB health probes — always present
ALLOWED_HOSTS.extend(h for h in ("localhost", "127.0.0.1") if h not in ALLOWED_HOSTS)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="writing_hub_db"),
        "USER": config("DB_USER", default="writing_hub"),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default="writing_hub_db"),
        "PORT": config("DB_PORT", default="5432"),
        "CONN_MAX_AGE": 60,
    }
}

# SSL is terminated by Cloudflare/Nginx — Django must NOT redirect
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

CSRF_TRUSTED_ORIGINS = [
    "https://writing.iil.pet",
]
