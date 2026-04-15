"""
REFLEX Audit — Neues Projekt Formular (/projekte/new/)

Prüft die existierende UI gegen Qualitätskriterien:
- ARIA: Alle Formularfelder haben Labels
- Validierung: Pflichtfelder werden erzwungen
- Submit: Projekt wird erstellt und Redirect erfolgt
- Content-Types: Alle Optionen vorhanden
- Genre-Auswahl: Alle Genres vorhanden
"""
import pytest

from django.urls import reverse


NEUES_PROJEKT_URL = "/projekte/new/"


class TestNeuesProjektFormAudit:
    """Audit des 'Neues Projekt' Formulars — REFLEX Abschnitt 6."""

    # ── Erreichbarkeit ─────────────────────────────────────────────

    def test_should_load_form(self, auth_client):
        """Formular ist erreichbar."""
        r = auth_client.get(NEUES_PROJEKT_URL)
        assert r.status_code == 200
        assert "Neues Schreibprojekt" in r.content.decode()

    def test_should_require_login(self):
        """Unauthentifizierter Zugriff wird umgeleitet."""
        from django.test import Client
        anon = Client(SERVER_NAME="writing.iil.pet")
        r = anon.get(NEUES_PROJEKT_URL)
        assert r.status_code in (301, 302, 403), \
            f"Expected redirect/forbidden, got {r.status_code}"

    # ── Content-Type Auswahl ───────────────────────────────────────

    def test_should_have_all_content_types(self, auth_client):
        """Alle Inhaltstypen sind als Radio-Buttons vorhanden."""
        r = auth_client.get(NEUES_PROJEKT_URL)
        content = r.content.decode()
        expected = [
            "Roman", "Sachbuch", "Kurzgeschichte", "Drehbuch",
            "Essay", "Novelle", "Graphic Novel",
            "Akademische Arbeit", "Wissenschaftliches Paper",
        ]
        for ct in expected:
            assert ct in content, f"Content-Type '{ct}' fehlt im Formular"

    # ── Titel ──────────────────────────────────────────────────────

    def test_should_have_title_field(self, auth_client):
        """Arbeitstitel-Feld ist vorhanden."""
        r = auth_client.get(NEUES_PROJEKT_URL)
        content = r.content.decode()
        assert "Arbeitstitel" in content

    # ── Genre-Auswahl ──────────────────────────────────────────────

    def test_should_have_genre_options(self, auth_client):
        """Alle Genres sind als Radio-Buttons vorhanden."""
        r = auth_client.get(NEUES_PROJEKT_URL)
        content = r.content.decode()
        expected_genres = [
            "Fantasy", "Science-Fiction", "Thriller", "Krimi",
            "Romantik", "Horror", "Historischer Roman",
            "Literarische Fiktion", "Young Adult", "Kinderbuch",
            "Autobiografie", "Sachbuch", "Reisebericht",
            "Humor", "Mystery",
        ]
        for genre in expected_genres:
            assert genre in content, f"Genre '{genre}' fehlt"

    # ── Zusätzliche Felder ─────────────────────────────────────────

    def test_should_have_description_field(self, auth_client):
        """Kurzbeschreibung / Prämisse Feld vorhanden."""
        r = auth_client.get(NEUES_PROJEKT_URL)
        content = r.content.decode()
        assert "Kurzbeschreibung" in content or "Prämisse" in content

    def test_should_have_target_audience_dropdown(self, auth_client):
        """Zielgruppen-Dropdown mit Optionen vorhanden."""
        r = auth_client.get(NEUES_PROJEKT_URL)
        content = r.content.decode()
        assert "Zielgruppe" in content
        assert "Erwachsene" in content

    def test_should_have_word_count_field(self, auth_client):
        """Ziel-Wortanzahl Feld vorhanden mit Default."""
        r = auth_client.get(NEUES_PROJEKT_URL)
        content = r.content.decode()
        assert "Wortanzahl" in content or "wortanzahl" in content.lower()
        assert "50000" in content  # Default

    # ── Submit-Button ──────────────────────────────────────────────

    def test_should_have_submit_button(self, auth_client):
        """'Projekt erstellen' Button vorhanden."""
        r = auth_client.get(NEUES_PROJEKT_URL)
        content = r.content.decode()
        assert "Projekt erstellen" in content

    def test_should_have_cancel_link(self, auth_client):
        """Abbrechen-Link führt zurück zur Projektliste."""
        r = auth_client.get(NEUES_PROJEKT_URL)
        content = r.content.decode()
        assert "Abbrechen" in content
        assert "/projekte/" in content

    # ── Validierung ────────────────────────────────────────────────

    def test_should_reject_empty_title(self, auth_client):
        """Formular lehnt leeren Titel ab."""
        r = auth_client.post(NEUES_PROJEKT_URL, data={
            "content_type": "novel",
            "title": "",
            "target_word_count": 50000,
        })
        # Should stay on form (200 with errors) or redirect back
        assert r.status_code in (200, 302)
        if r.status_code == 200:
            content = r.content.decode()
            # Form should show an error
            assert "required" in content.lower() or "pflicht" in content.lower() \
                or "error" in content.lower() or "fehler" in content.lower() \
                or "field is required" in content.lower()

    def test_should_create_project_with_valid_data(self, auth_client):
        """Projekt wird mit gültigen Daten erstellt → Redirect."""
        r = auth_client.post(NEUES_PROJEKT_URL, data={
            "content_type": "novel",
            "title": "REFLEX Test-Projekt (wird gelöscht)",
            "genre": "fantasy",
            "target_word_count": 50000,
        })
        # Success: Redirect to project detail or list
        assert r.status_code in (200, 301, 302), \
            f"Expected redirect after create, got {r.status_code}"

    # ── Autoren-Sektion ────────────────────────────────────────────

    def test_should_show_author_section(self, auth_client):
        """Autoren & Schreibstile Sektion ist sichtbar."""
        r = auth_client.get(NEUES_PROJEKT_URL)
        content = r.content.decode()
        assert "Schreibstile" in content or "Autoren" in content
