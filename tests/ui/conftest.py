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

@pytest.fixture
def auth_client(db):
    """Authenticated Django test client.

    Uses force_login — no credentials, no browser, fast.
    Works with SERVER_NAME to avoid DisallowedHost.
    Seeds a test user + lookup data if none exists.
    """
    User = get_user_model()
    user = User.objects.first()
    if not user:
        user = User.objects.create_superuser(
            username="reflex-test",
            email="test@iil.gmbh",
            password="test",
        )

    _seed_lookup_data()

    c = Client(SERVER_NAME="writing.iil.pet")
    c.force_login(user)
    return c


def _seed_lookup_data():
    """Seed lookup tables for UI audit tests (REFLEX Zirkel 2)."""
    from apps.projects.models import ContentTypeLookup, GenreLookup, AudienceLookup

    if not ContentTypeLookup.objects.exists():
        for i, (name, slug) in enumerate([
            ("Roman", "novel"), ("Sachbuch", "nonfiction"),
            ("Kurzgeschichte", "short_story"), ("Drehbuch", "screenplay"),
            ("Essay", "essay"), ("Novelle", "novella"),
            ("Graphic Novel", "graphic_novel"),
            ("Akademische Arbeit", "academic"),
            ("Wissenschaftliches Paper", "scientific"),
        ]):
            ContentTypeLookup.objects.create(name=name, slug=slug, order=i)

    if not GenreLookup.objects.exists():
        for i, name in enumerate([
            "Fantasy", "Science-Fiction", "Thriller", "Krimi", "Romantik",
            "Horror", "Historischer Roman", "Literarische Fiktion",
            "Young Adult", "Kinderbuch", "Autobiografie", "Sachbuch",
            "Reisebericht", "Humor", "Mystery",
        ]):
            GenreLookup.objects.create(name=name, order=i)

    if not AudienceLookup.objects.exists():
        for i, name in enumerate([
            "Erwachsene", "Young Adult", "Kinder (8-12)",
            "Kleinkinder (3-7)", "Fachpublikum", "Allgemein",
        ]):
            AudienceLookup.objects.create(name=name, order=i)

    # Outline Frameworks (identisch mit Production)
    from apps.projects.models import OutlineFramework
    if not OutlineFramework.objects.exists():
        from django.core.management import call_command
        call_command("seed_outline_frameworks", verbosity=0)

    from apps.projects.models import BookProject
    User = get_user_model()
    owner = User.objects.first()
    if owner and not BookProject.objects.exists():
        BookProject.objects.create(
            title="Testprojekt für REFLEX",
            owner=owner,
            content_type="novel",
            genre="Fantasy",
            target_word_count=50000,
        )


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
