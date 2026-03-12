"""
Writing Hub — Test Settings (ADR-141: PostgreSQL-Only Testing)
"""
import os

from .base import *  # noqa: F401, F403

DEBUG = False

# ADR-141: Explicit PostgreSQL — SQLite is BANNED for testing
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("TEST_DB_NAME", "writing_hub_test"),
        "USER": os.environ.get("TEST_DB_USER", "dehnert"),
        "PASSWORD": os.environ.get("TEST_DB_PASSWORD", ""),
        "HOST": os.environ.get("TEST_DB_HOST", "localhost"),
        "PORT": os.environ.get("TEST_DB_PORT", "5434"),
        "TEST": {"NAME": "test_writing_hub"},
    }
}

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
