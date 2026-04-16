"""
REFLEX Audit — Charakter-Views (Phase 1: Speed Matters)

Prüft die Charakter-UI gegen Qualitätskriterien:
- Welten-Liste erreichbar
- Welt-Detail zeigt Charakter-Karten (Kurzprofil)
- Charakter-Erstellen: Formular enthält neue Felder (voice_pattern, secret)
- Charakter-Karten: narrative_role Badge, voice_pattern, secret Indikator
- Charakter-Verknüpfen: View erreichbar
- CSRF-Token in allen POST-Formularen
- Felder-Reihenfolge im Formular korrekt

Jeder View-Test hat @reflex_link → generiert klickbare Links in
tests/ui/feedback/reflex-links.md nach dem Testlauf.
"""
import uuid

import pytest
from django.urls import reverse

from .conftest import reflex_link


def _seed_world_with_character(db):
    """Seed a project + world link + character link for testing."""
    from django.contrib.auth import get_user_model
    from apps.projects.models import BookProject
    from apps.worlds.models import ProjectWorldLink, ProjectCharacterLink

    User = get_user_model()
    user = User.objects.first()
    if not user:
        user = User.objects.create_superuser(
            username="reflex-test", email="test@iil.gmbh", password="test",
        )

    project = BookProject.objects.filter(owner=user).first()
    if not project:
        project = BookProject.objects.create(
            title="Speed Matters",
            owner=user,
            content_type="novel",
            genre="Thriller",
            target_word_count=80000,
        )

    world_link = ProjectWorldLink.objects.filter(project=project).first()
    if not world_link:
        world_link = ProjectWorldLink.objects.create(
            project=project,
            weltenhub_world_id=uuid.uuid4(),
            role="primary",
        )

    char_link = ProjectCharacterLink.objects.filter(project=project).first()
    if not char_link:
        char_link = ProjectCharacterLink.objects.create(
            project=project,
            weltenhub_character_id=uuid.uuid4(),
            narrative_role="protagonist",
            voice_pattern="Kurze, abgehackte Saetze. Kein Smalltalk. Schwarzer Humor als Ventil.",
            secret_what="Kennt die Wahrheit ueber den Einsatz vor drei Jahren",
            secret_from_whom="BKA-Fuehrung",
            secret_why="Wuerde ihre Rehabilitierung gefaehrden",
            character_status="alive",
            first_appearance="Kapitel 1",
            want="Den alten Einsatz verstehen",
            need="Wieder vertrauen lernen",
            flaw="Kontrollzwang",
        )

    return project, world_link, char_link


# ═══════════════════════════════════════════════════════════════════════
# Welten-Liste
# ═══════════════════════════════════════════════════════════════════════

WELTEN_URL = "/welten/"


@pytest.mark.django_db
class TestWeltenListeAudit:
    """Welten-Übersicht ist erreichbar."""

    @reflex_link("/welten/", "Welten-Uebersicht")
    def test_should_load_welten_liste(self, auth_client):
        """Welten-Liste liefert HTTP 200."""
        r = auth_client.get(WELTEN_URL)
        assert r.status_code == 200

    @reflex_link("/projekte/", "Nav-Link zu /welten/ vorhanden")
    def test_should_have_welten_nav_link(self, auth_client):
        """/welten/ ist in der Navigation enthalten."""
        r = auth_client.get("/projekte/")
        assert "/welten/" in r.content.decode()


# ═══════════════════════════════════════════════════════════════════════
# Charakter-Erstellen — Formular-Audit
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestCharacterCreateFormAudit:
    """Charakter-Erstellformular enthält alle Phase-1-Felder."""

    @pytest.fixture(autouse=True)
    def setup(self, db, auth_client):
        self.project, self.world_link, self.char_link = _seed_world_with_character(db)
        self.client = auth_client
        self.url = reverse("worlds_html:character_create", kwargs={"pk": self.world_link.pk})

    @reflex_link("/welten/<uuid>/characters/create/", "Charakter erstellen")
    def test_should_reach_character_create(self):
        """Charakter-Erstellen ist erreichbar (WeltenHub-Fehler = ok, Form muss rendern)."""
        r = self.client.get(self.url)
        assert r.status_code == 200

    def test_should_have_name_field(self):
        """Pflichtfeld 'Name' ist vorhanden."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert 'name="name"' in content

    def test_should_have_personality_field(self):
        """Feld 'Persoenlichkeit' ist vorhanden."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert 'name="personality"' in content

    def test_should_have_voice_pattern_field(self):
        """Neues Feld 'Stimme / Sprechmuster' ist im Formular."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert 'name="voice_pattern"' in content
        assert "Sprechmuster" in content

    def test_should_have_secret_fields(self):
        """Geheimnis-Felder (Was, Vor wem, Warum) sind im Formular."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert 'name="secret_what"' in content
        assert 'name="secret_from_whom"' in content
        assert 'name="secret_why"' in content

    def test_should_have_backstory_field(self):
        """Feld 'Hintergrund / Backstory' ist vorhanden."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert 'name="backstory"' in content

    def test_should_have_goals_and_fears_fields(self):
        """Felder 'Ziele' und 'Aengste' sind vorhanden."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert 'name="goals"' in content
        assert 'name="fears"' in content

    def test_should_have_protagonist_checkbox(self):
        """Protagonist-Checkbox ist vorhanden."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert 'name="is_protagonist"' in content

    def test_should_have_submit_button(self):
        """Erstellen-Button vorhanden."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert "Charakter erstellen" in content or 'type="submit"' in content

    def test_should_have_csrf_token(self):
        """CSRF-Token ist im Formular vorhanden."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert "csrfmiddlewaretoken" in content

    def test_should_have_correct_field_order(self):
        """Felder in logischer Reihenfolge: Name → Basis → Stimme → Geheimnis → Notizen."""
        r = self.client.get(self.url)
        content = r.content.decode()
        name_pos = content.find('name="name"')
        personality_pos = content.find('name="personality"')
        voice_pos = content.find('name="voice_pattern"')
        secret_pos = content.find('name="secret_what"')
        notes_pos = content.find('name="notes"')
        assert name_pos < personality_pos < voice_pos < secret_pos < notes_pos, \
            "Felder-Reihenfolge stimmt nicht: Name < Personality < Voice < Secret < Notes"

    def test_should_require_login(self):
        """Unauthentifizierter Zugriff wird zu Login umgeleitet."""
        from django.test import Client
        anon = Client(SERVER_NAME="writing.iil.pet")
        r = anon.get(self.url)
        assert r.status_code == 302
        assert "/accounts/" in r.url or "/login" in r.url


# ═══════════════════════════════════════════════════════════════════════
# Charakter-Verknüpfen — View erreichbar
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestCharacterLinkViewAudit:
    """Charakter-Verknüpfen-View ist erreichbar."""

    @pytest.fixture(autouse=True)
    def setup(self, db, auth_client):
        self.project, self.world_link, _ = _seed_world_with_character(db)
        self.client = auth_client

    @reflex_link("/welten/<uuid>/characters/link/", "Charakter verknuepfen")
    def test_should_reach_character_link(self):
        """Charakter-Verknüpfen liefert HTTP 200."""
        url = reverse("worlds_html:character_link", kwargs={"pk": self.world_link.pk})
        r = self.client.get(url)
        assert r.status_code == 200


# ═══════════════════════════════════════════════════════════════════════
# Welt-Detail — Charakter-Karten Kurzprofil
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestWorldDetailCharacterCardsAudit:
    """Welt-Detail zeigt Charakter-Karten mit neuen Feldern."""

    @pytest.fixture(autouse=True)
    def setup(self, db, auth_client):
        self.project, self.world_link, self.char_link = _seed_world_with_character(db)
        self.client = auth_client
        self.url = reverse("worlds_html:detail", kwargs={"pk": self.world_link.pk})

    @reflex_link("/welten/<uuid>/", "Welt-Detail mit Charakter-Karten")
    def test_should_reach_world_detail(self):
        """Welt-Detail liefert HTTP 200 (auch wenn WeltenHub nicht erreichbar)."""
        r = self.client.get(self.url)
        assert r.status_code == 200

    def test_should_show_character_section(self):
        """Charaktere-Sektion ist im Template vorhanden."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert "Charaktere" in content

    def test_should_have_create_button(self):
        """'Neuer Charakter' Button ist vorhanden."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert "Neuer Charakter" in content

    def test_should_have_link_button(self):
        """'Vorhandene verknuepfen' Button ist vorhanden."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert "verknuepfen" in content.lower()

    def test_should_have_llm_generate_button(self):
        """'Per LLM generieren' Button ist vorhanden."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert "LLM generieren" in content


# ═══════════════════════════════════════════════════════════════════════
# ProjectCharacterLink Model — Feld-Audit
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestCharacterModelFieldsAudit:
    """ProjectCharacterLink hat alle Phase-1-Felder."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        _, _, self.char_link = _seed_world_with_character(db)

    def test_should_have_voice_pattern(self):
        """voice_pattern ist gesetzt und abrufbar."""
        assert self.char_link.voice_pattern != ""
        assert "Kurze" in self.char_link.voice_pattern

    def test_should_have_secret_what(self):
        """secret_what ist gesetzt."""
        assert "Wahrheit" in self.char_link.secret_what

    def test_should_have_secret_from_whom(self):
        """secret_from_whom ist gesetzt."""
        assert self.char_link.secret_from_whom != ""

    def test_should_have_secret_why(self):
        """secret_why ist gesetzt."""
        assert self.char_link.secret_why != ""

    def test_should_have_character_status(self):
        """character_status default = alive."""
        assert self.char_link.character_status == "alive"
        assert self.char_link.get_character_status_display() == "Lebt"

    def test_should_have_first_appearance(self):
        """first_appearance ist gesetzt."""
        assert self.char_link.first_appearance == "Kapitel 1"

    def test_should_have_narrative_role_protagonist(self):
        """narrative_role = protagonist."""
        assert self.char_link.narrative_role == "protagonist"
        assert "Protagonist" in self.char_link.get_narrative_role_display()

    def test_should_have_arc_fields(self):
        """Want/Need/Flaw aus ADR-152 sind gesetzt."""
        assert self.char_link.want != ""
        assert self.char_link.need != ""
        assert self.char_link.flaw != ""

    def test_should_have_character_status_choices(self):
        """CHARACTER_STATUS hat 4 Optionen."""
        from apps.worlds.models import ProjectCharacterLink
        assert len(ProjectCharacterLink.CHARACTER_STATUS) == 4
        keys = [k for k, _ in ProjectCharacterLink.CHARACTER_STATUS]
        assert "alive" in keys
        assert "dead" in keys
        assert "missing" in keys
        assert "unknown" in keys

    def test_should_have_12_narrative_roles(self):
        """NARRATIVE_ROLES hat 12 Optionen (ADR-157)."""
        from apps.worlds.models import ProjectCharacterLink
        assert len(ProjectCharacterLink.NARRATIVE_ROLES) == 12

    def test_should_persist_and_reload(self):
        """Felder ueberleben save/reload."""
        from apps.worlds.models import ProjectCharacterLink
        reloaded = ProjectCharacterLink.objects.get(pk=self.char_link.pk)
        assert reloaded.voice_pattern == self.char_link.voice_pattern
        assert reloaded.secret_what == self.char_link.secret_what
        assert reloaded.character_status == "alive"
        assert reloaded.first_appearance == "Kapitel 1"


# ═══════════════════════════════════════════════════════════════════════
# Autoren / Schreibstile — Genre-Profil Audit
# ═══════════════════════════════════════════════════════════════════════

AUTOREN_URL = "/autoren/"


@pytest.mark.django_db
class TestAutorenGenreAudit:
    """Autoren-Bereich ist erreichbar und Genre-Modelle existieren."""

    @reflex_link("/autoren/", "Autoren-Uebersicht")
    def test_should_load_autoren_liste(self, auth_client):
        """Autoren-Liste liefert HTTP 200."""
        r = auth_client.get(AUTOREN_URL)
        assert r.status_code == 200

    def test_should_have_genre_profile_model(self, db):
        """GenreProfile-Modell ist importierbar und hat Felder."""
        from apps.authors.models import GenreProfile
        assert hasattr(GenreProfile, "slug")
        assert hasattr(GenreProfile, "name_short")
        assert hasattr(GenreProfile, "icon")
        assert hasattr(GenreProfile, "situation_count")

    def test_should_have_situation_type_model(self, db):
        """SituationType-Modell hat llm_prompt_hint."""
        from apps.authors.models import SituationType
        assert hasattr(SituationType, "slug")
        assert hasattr(SituationType, "label")
        assert hasattr(SituationType, "llm_prompt_hint")
        assert hasattr(SituationType, "genre_profile")


# ═══════════════════════════════════════════════════════════════════════
# Anon-Zugriff — alle Views hinter Login
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestAnonAccessDenied:
    """Unauthentifizierter Zugriff auf Charakter-Views wird umgeleitet."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        _, self.world_link, _ = _seed_world_with_character(db)
        from django.test import Client
        self.anon = Client(SERVER_NAME="writing.iil.pet")

    def test_should_redirect_welten_liste(self):
        r = self.anon.get("/welten/")
        assert r.status_code == 302

    def test_should_redirect_welt_detail(self):
        url = reverse("worlds_html:detail", kwargs={"pk": self.world_link.pk})
        r = self.anon.get(url)
        assert r.status_code == 302

    def test_should_redirect_character_create(self):
        url = reverse("worlds_html:character_create", kwargs={"pk": self.world_link.pk})
        r = self.anon.get(url)
        assert r.status_code == 302

    def test_should_redirect_character_link(self):
        url = reverse("worlds_html:character_link", kwargs={"pk": self.world_link.pk})
        r = self.anon.get(url)
        assert r.status_code == 302
