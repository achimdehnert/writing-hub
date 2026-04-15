"""
REFLEX UI Tests — conftest.py

Auth: Two strategies depending on execution context:
  1. Cascade/MCP:  /dev-login/ signed token (no credentials needed)
  2. Local/CI:     Session Storage from .env.test credentials

Session Storage is reused across the entire test run.
If the session expires, it is automatically renewed.
"""
import os
import json
import logging
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core import signing
from django.test import Client

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────
AUTH_DIR = Path(__file__).parent / ".auth"
SNAPSHOT_DIR = Path(__file__).parent / "snapshots"
FEEDBACK_DIR = Path(__file__).parent / "feedback"

BASE_URL = os.environ.get("REFLEX_BASE_URL", "https://writing.iil.pet")


# ── Django Test Client Fixture (primary — no browser needed) ──────────────

@pytest.fixture(scope="session")
def django_client():
    """Authenticated Django test client.

    Uses force_login — no credentials, no browser, fast.
    Works with SERVER_NAME to avoid DisallowedHost.
    """
    User = get_user_model()
    user = (
        User.objects.filter(is_superuser=True).first()
        or User.objects.first()
    )
    assert user, "No users in database — run seed first"

    c = Client(SERVER_NAME="writing.iil.pet")
    c.force_login(user)
    return c


@pytest.fixture
def auth_client(django_client):
    """Alias for session-scoped django_client."""
    return django_client


# ── Signed Token Helper (for Playwright MCP / external browsers) ─────────

def generate_dev_login_url(next_url="/projekte/"):
    """Generate a signed auto-login URL (5 min TTL).

    Use this to authenticate Playwright MCP or external browsers.
    """
    User = get_user_model()
    user = (
        User.objects.filter(is_superuser=True).first()
        or User.objects.first()
    )
    assert user, "No users in database"
    token = signing.dumps({"uid": str(user.pk), "next": next_url})
    return f"/dev-login/?token={token}"


# ── Snapshot Helpers ─────────────────────────────────────────────────────

def save_snapshot(name: str, content: str) -> Path:
    """Save an ARIA or HTML snapshot for diffing."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SNAPSHOT_DIR / f"{name}.yaml"
    path.write_text(content, encoding="utf-8")
    return path


def save_feedback(uc_slug: str, version: int, data: dict) -> Path:
    """Save REFLEX feedback.json."""
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    path = FEEDBACK_DIR / f"{uc_slug}.v{version}.feedback.json"
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path
