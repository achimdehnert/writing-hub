"""
REFLEX UI Tests — conftest.py

Auth: Two strategies depending on execution context:
  1. Cascade/MCP:  /dev-login/ signed token (no credentials needed)
  2. Local/CI:     Session Storage from .env.test credentials

Session Storage is reused across the entire test run.
If the session expires, it is automatically renewed.

Link Report:
  After each test run, generates tests/ui/feedback/reflex-links.md
  with clickable URLs for every tested page — open in browser to verify manually.
"""

import os
import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
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
REPORT_DIR = Path(__file__).parent / "feedback"

BASE_URL = os.environ.get("REFLEX_BASE_URL", "http://localhost:8000")


# ═══════════════════════════════════════════════════════════════════════════
# REFLEX Link Collector — tracks tested URLs per test class
# ═══════════════════════════════════════════════════════════════════════════


class ReflexLinkCollector:
    """Collects tested URLs and generates a clickable report."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.entries: list[dict] = []

    def add(self, path: str, test_name: str, test_class: str = "", status: str = "passed", description: str = ""):
        self.entries.append(
            {
                "path": path,
                "url": f"{self.base_url}{path}",
                "test_name": test_name,
                "test_class": test_class,
                "status": status,
                "description": description,
            }
        )

    def generate_markdown(self) -> str:
        """Generate a markdown report with clickable links."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines = [
            "# REFLEX Link Report — writing-hub",
            "",
            f"Generated: {now}  ",
            f"Base URL: {self.base_url}  ",
            f"Tests: {len(self.entries)} URLs geprüft",
            "",
            "---",
            "",
        ]

        # Group by test class
        by_class = defaultdict(list)
        for e in self.entries:
            by_class[e["test_class"] or "Uncategorized"].append(e)

        for cls_name, entries in by_class.items():
            lines.append(f"## {cls_name}")
            lines.append("")
            for e in entries:
                icon = "✅" if e["status"] == "passed" else "❌"
                desc = f" — {e['description']}" if e["description"] else ""
                lines.append(f"- {icon} [{e['path']}]({e['url']}){desc}")
            lines.append("")

        # Quick-open section
        lines.append("---")
        lines.append("")
        lines.append("## Quick-Open Links (Clipboard-ready)")
        lines.append("")
        seen = set()
        for e in self.entries:
            if e["path"] not in seen:
                seen.add(e["path"])
                lines.append("```")
                lines.append(e["url"])
                lines.append("```")
        lines.append("")

        return "\n".join(lines)

    def save(self, path: Path | None = None) -> Path:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        out = path or REPORT_DIR / "reflex-links.md"
        out.write_text(self.generate_markdown(), encoding="utf-8")
        return out


# Global collector instance
_link_collector = ReflexLinkCollector(BASE_URL)


def reflex_link(path: str, description: str = ""):
    """Pytest marker decorator: register a tested URL for the link report.

    Usage in tests:
        @reflex_link("/welten/", "Welten-Übersicht")
        def test_should_load_welten_liste(self, auth_client):
            ...
    """

    def decorator(func):
        func._reflex_path = path
        func._reflex_desc = description
        return func

    return decorator


@pytest.fixture(autouse=True)
def _reflex_link_tracker(request):
    """Auto-fixture: after each test, record URL if @reflex_link was used."""
    yield
    test_fn = request.function
    path = getattr(test_fn, "_reflex_path", None)
    if path:
        cls_name = request.node.parent.name if request.node.parent else ""
        _link_collector.add(
            path=path,
            test_name=request.node.name,
            test_class=cls_name,
            status="passed" if not request.node.rep_call or request.node.rep_call.passed else "failed",
            description=getattr(test_fn, "_reflex_desc", ""),
        )


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Store test outcome on the item for _reflex_link_tracker."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


def pytest_sessionfinish(session, exitstatus):
    """Generate link report at end of test session."""
    if _link_collector.entries:
        report_path = _link_collector.save()
        # Print summary to terminal
        print(f"\n{'=' * 60}")
        print(f"REFLEX Link Report: {report_path}")
        print(f"{'=' * 60}")
        seen = set()
        for e in _link_collector.entries:
            if e["path"] not in seen:
                seen.add(e["path"])
                icon = "✅" if e["status"] == "passed" else "❌"
                print(f"  {icon} {e['url']}")
        print(f"{'=' * 60}\n")


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
        for i, (name, slug) in enumerate(
            [
                ("Roman", "novel"),
                ("Sachbuch", "nonfiction"),
                ("Kurzgeschichte", "short_story"),
                ("Drehbuch", "screenplay"),
                ("Essay", "essay"),
                ("Novelle", "novella"),
                ("Graphic Novel", "graphic_novel"),
                ("Akademische Arbeit", "academic"),
                ("Wissenschaftliches Paper", "scientific"),
            ]
        ):
            ContentTypeLookup.objects.create(name=name, slug=slug, order=i)

    if not GenreLookup.objects.exists():
        for i, name in enumerate(
            [
                "Fantasy",
                "Science-Fiction",
                "Thriller",
                "Krimi",
                "Romantik",
                "Horror",
                "Historischer Roman",
                "Literarische Fiktion",
                "Young Adult",
                "Kinderbuch",
                "Autobiografie",
                "Sachbuch",
                "Reisebericht",
                "Humor",
                "Mystery",
            ]
        ):
            GenreLookup.objects.create(name=name, order=i)

    if not AudienceLookup.objects.exists():
        for i, name in enumerate(
            [
                "Erwachsene",
                "Young Adult",
                "Kinder (8-12)",
                "Kleinkinder (3-7)",
                "Fachpublikum",
                "Allgemein",
            ]
        ):
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
    user = User.objects.filter(is_superuser=True).first() or User.objects.first()
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
