"""
Writing Hub — Test Settings (ADR-141: PostgreSQL-Only Testing)
"""

import os

from .base import *  # noqa: F401, F403
from decouple import config

DEBUG = False
ALLOWED_HOSTS = ["*"]

# CI migration check: USE_POSTGRES=0 → SQLite in-memory (graph check only)
if os.environ.get("USE_POSTGRES", "1") == "0":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
else:
    # ADR-141: Explicit PostgreSQL — SQLite is BANNED for testing
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("TEST_DB_NAME", default="writing_hub_test"),
            "USER": config("TEST_DB_USER", default="dehnert"),
            "PASSWORD": config("TEST_DB_PASSWORD", default=""),
            "HOST": config("TEST_DB_HOST", default="localhost"),
            "PORT": config("TEST_DB_PORT", default="5434"),
            "TEST": {"NAME": "test_writing_hub"},
        }
    }

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
