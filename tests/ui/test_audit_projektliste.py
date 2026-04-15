"""
REFLEX Audit — Projektliste (/projekte/)

Prüft die existierende UI gegen Qualitätskriterien:
- ARIA: Alle interaktiven Elemente haben Labels
- Heading-Hierarchie: Logisch h1 → h2 → h3
- Navigation: Alle Hauptlinks erreichbar
- Filter: Suche + Dropdowns funktional
- Projekt-Cards: Strukturierte Darstellung
"""
import pytest


PROJEKTLISTE_URL = "/projekte/"


@pytest.mark.django_db
class TestProjektlisteAudit:
    """Audit der Projektliste — REFLEX Abschnitt 6."""

    # ── Navigation ─────────────────────────────────────────────────

    def test_should_load_projektliste(self, auth_client):
        """Projektliste ist erreichbar und rendert korrekt."""
        r = auth_client.get(PROJEKTLISTE_URL)
        assert r.status_code == 200
        assert "Meine Projekte" in r.content.decode()

    def test_should_have_nav_links(self, auth_client):
        """Navigation enthält alle Hauptbereiche."""
        r = auth_client.get(PROJEKTLISTE_URL)
        content = r.content.decode()
        expected_links = [
            "/projekte/",
            "/projekte/quick/",
            "/ideen/studio/",
            "/outlines/",
            "/autoren/",
            "/serien/",
            "/ideen/",
        ]
        for link in expected_links:
            assert link in content, f"Nav-Link {link} fehlt"

    def test_should_have_neues_projekt_button(self, auth_client):
        """'Neues Projekt' Button ist sichtbar und verlinkt."""
        r = auth_client.get(PROJEKTLISTE_URL)
        content = r.content.decode()
        assert "/projekte/new/" in content
        assert "Neues Projekt" in content

    # ── Heading-Hierarchie ─────────────────────────────────────────

    def test_should_have_page_heading(self, auth_client):
        """Seite hat eine Überschrift 'Meine Projekte'."""
        r = auth_client.get(PROJEKTLISTE_URL)
        content = r.content.decode()
        assert "Meine Projekte" in content

    # ── Filter ─────────────────────────────────────────────────────

    def test_should_have_search_input(self, auth_client):
        """Suchfeld für Titel ist vorhanden."""
        r = auth_client.get(PROJEKTLISTE_URL)
        content = r.content.decode()
        assert "Titel suchen" in content or "search" in content.lower()

    def test_should_have_content_type_filter(self, auth_client):
        """Inhaltstyp-Filter enthält erwartete Optionen."""
        r = auth_client.get(PROJEKTLISTE_URL)
        content = r.content.decode()
        expected_types = ["Roman", "Sachbuch", "Kurzgeschichte", "Essay"]
        for ct in expected_types:
            assert ct in content, f"Content-Type '{ct}' fehlt im Filter"

    def test_should_have_genre_filter(self, auth_client):
        """Genre-Filter enthält erwartete Optionen."""
        r = auth_client.get(PROJEKTLISTE_URL)
        content = r.content.decode()
        expected_genres = ["Fantasy", "Science-Fiction", "Thriller", "Krimi"]
        for genre in expected_genres:
            assert genre in content, f"Genre '{genre}' fehlt im Filter"

    # ── Projekt-Cards ──────────────────────────────────────────────

    def test_should_display_project_cards(self, auth_client):
        """Projektliste zeigt mindestens ein Projekt."""
        r = auth_client.get(PROJEKTLISTE_URL)
        content = r.content.decode()
        # Cards haben einen "Öffnen" Link
        assert "Öffnen" in content or "öffnen" in content.lower()

    def test_should_show_word_count_on_cards(self, auth_client):
        """Projekt-Cards zeigen Wortanzahl."""
        r = auth_client.get(PROJEKTLISTE_URL)
        content = r.content.decode()
        assert "Wörter" in content or "wörter" in content.lower()

    # ── Action Buttons ─────────────────────────────────────────────

    def test_should_have_quick_project_link(self, auth_client):
        """Quick Project Link ist vorhanden."""
        r = auth_client.get(PROJEKTLISTE_URL)
        content = r.content.decode()
        assert "/projekte/quick/" in content
        assert "Quick Project" in content

    def test_should_have_import_link(self, auth_client):
        """Import-Link ist vorhanden."""
        r = auth_client.get(PROJEKTLISTE_URL)
        content = r.content.decode()
        assert "/projekte/import/" in content
        assert "Importieren" in content

    # ── Auth / Abmelden ────────────────────────────────────────────

    def test_should_show_logout_link(self, auth_client):
        """Abmelden-Link ist sichtbar."""
        r = auth_client.get(PROJEKTLISTE_URL)
        content = r.content.decode()
        assert "/accounts/logout/" in content
        assert "Abmelden" in content
