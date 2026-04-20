"""Build-time settings for Docker collectstatic + CI migration check.

No database, no Redis — just enough to run management commands.
ADR-083: No || true, no dummy env vars.
"""

from .base import *  # noqa: F401,F403

SECRET_KEY = "build-dummy-not-used-in-production"

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
