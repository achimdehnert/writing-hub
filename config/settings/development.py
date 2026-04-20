"""
Writing Hub — Development Settings
"""

import os
from pathlib import Path as _Path

from .base import *  # noqa: F401, F403

DEBUG = True

# ── Shared Secrets (ADR-159) ──────────────────────────────────────────────
_SECRETS_DIR = _Path.home() / "shared" / "secrets"


def _read_secret(name: str) -> str:
    """Read a secret from shared secrets dir, return empty string if missing."""
    p = _SECRETS_DIR / name
    return p.read_text().strip() if p.exists() else ""


# Set as Django settings AND env vars (litellm reads os.environ directly)
OPENAI_API_KEY = _read_secret("openai_api_key")  # noqa: F405
GROQ_API_KEY = _read_secret("groq_api_key")  # noqa: F405
if OPENAI_API_KEY:
    os.environ.setdefault("OPENAI_API_KEY", OPENAI_API_KEY)
if GROQ_API_KEY:
    os.environ.setdefault("GROQ_API_KEY", GROQ_API_KEY)

ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:*",
    "http://127.0.0.1:*",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "writing_hub_test",
        "USER": "dehnert",
        "PASSWORD": "test",
        "HOST": "127.0.0.1",
        "PORT": "5434",
    }
}

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
