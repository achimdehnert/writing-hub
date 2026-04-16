"""
REFLEX Zirkel 2 — UI Audit: Projekt-Detailseite (UC-003)

Tests validieren AK-1 bis AK-16 der UC-003.
Nutzt Django Test Client (kein Playwright — schnell, DB-nah).
"""
import pytest
from django.urls import reverse


DETAIL_URL_NAME = "projects:detail"


def _seed_project(db):
    """Erzeugt ein Testprojekt mit Outline für die Detailseite."""
    from django.contrib.auth import get_user_model
    from apps.projects.models import BookProject, OutlineVersion, OutlineNode

    User = get_user_model()
    user = User.objects.first()
    if not user:
        user = User.objects.create_superuser(
            username="reflex-test", email="test@iil.gmbh", password="test",
        )

    project = BookProject.objects.filter(owner=user).first()
    if not project:
        project = BookProject.objects.create(
            title="REFLEX Testprojekt",
            owner=user,
            content_type="novel",
            genre="Thriller",
            target_word_count=50000,
            description="Ein Testprojekt für den REFLEX UI Audit.",
        )

    # Outline + Kapitel
    version = OutlineVersion.objects.filter(project=project, is_active=True).first()
    if not version:
        version = OutlineVersion.objects.create(
            project=project, name="Test-Outline", is_active=True, source="three_act",
        )
        for i in range(3):
            OutlineNode.objects.create(
                outline_version=version,
                title=f"Kapitel {i + 1}",
                order=i + 1,
                beat_type="chapter",
                word_count=1000 if i == 0 else 0,
            )
    return project, user


@pytest.mark.django_db
class TestProjektDetailAudit:
    """UI Audit Tests für die Projekt-Detailseite (UC-003)."""

    @pytest.fixture(autouse=True)
    def setup(self, db, auth_client):
        self.project, self.user = _seed_project(db)
        self.client = auth_client
        self.url = reverse(DETAIL_URL_NAME, kwargs={"pk": self.project.pk})

    # ── AK-1: HTTP 200 ───────────────────────────────────────────

    def test_should_load_detail_page(self):
        """AK-1: Seite lädt mit HTTP 200."""
        r = self.client.get(self.url)
        assert r.status_code == 200

    # ── AK-2: Titel ──────────────────────────────────────────────

    def test_should_show_project_title(self):
        """AK-2: Projekt-Titel wird angezeigt."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert self.project.title in content

    # ── AK-3: Navigation ─────────────────────────────────────────

    def test_should_have_back_link(self):
        """AK-3: 'Alle Projekte' Navigation ist vorhanden."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert "Alle Projekte" in content

    # ── AK-4 + AK-5: Quick-Action Buttons ────────────────────────

    def test_should_have_schreiben_button(self):
        """AK-4: Quick-Action 'Schreiben' ist vorhanden."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert "Schreiben" in content

    def test_should_have_health_button(self):
        """AK-5: Quick-Action 'Health' ist vorhanden."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert "/health/" in content

    # ── AK-6 + AK-7: Statistiken ────────────────────────────────

    def test_should_show_word_stats(self):
        """AK-6: Statistik 'Wörter' wird angezeigt."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert "Wörter" in content or "wörter" in content.lower()

    def test_should_show_chapter_stats(self):
        """AK-7: Statistik 'Kapitel' wird angezeigt."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert "Kapitel" in content

    # ── AK-8: Fortschritt ────────────────────────────────────────

    def test_should_show_progress_bar(self):
        """AK-8: Gesamtfortschritt-Balken ist vorhanden."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert "Gesamtfortschritt" in content

    # ── AK-9 bis AK-13: Workflow-Karten klickbar ─────────────────

    def test_should_have_lektorat_link(self):
        """AK-9: Workflow-Phase 'Lektorat' ist klickbar."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert "/lektorat/" in content
        assert "Lektorat" in content

    def test_should_have_review_link(self):
        """AK-10: Workflow-Phase 'Review' ist klickbar."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert "/review/" in content
        assert "Review" in content

    def test_should_have_publishing_link(self):
        """AK-11: Workflow-Phase 'Publishing' ist klickbar."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert "/publishing/" in content
        assert "Publishing" in content

    def test_should_have_export_link(self):
        """AK-12: Workflow-Phase 'Export' ist klickbar."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert "/export/" in content
        assert "Export" in content

    def test_should_have_konzept_link(self):
        """AK-13: Workflow-Phase 'Konzept' ist klickbar."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert "/edit/" in content
        assert "Konzept" in content

    # ── AK-14: Bearbeiten ────────────────────────────────────────

    def test_should_have_edit_button(self):
        """AK-14: Bearbeiten-Button ist vorhanden."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert "Bearbeiten" in content

    # ── AK-15: Outline-Bereich ───────────────────────────────────

    def test_should_show_outline_section(self):
        """AK-15: Outline-Bereich zeigt Kapitel."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert "Aktives Outline" in content
        assert "Kapitel 1" in content

    # ── AK-16: Sidebar ───────────────────────────────────────────

    def test_should_show_sidebar_sections(self):
        """AK-16: Sidebar zeigt Welten- und Charaktere-Bereich."""
        r = self.client.get(self.url)
        content = r.content.decode()
        assert "Welten" in content
        assert "Charaktere" in content

    # ── AK-17 + AK-18: Charaktere/Weltenbau klickbar ────────────

    def test_should_have_charaktere_onclick(self):
        """AK-17: Workflow-Karte 'Charaktere' ist klickbar (via <a> oder onclick)."""
        r = self.client.get(self.url)
        content = r.content.decode()
        workflow_start = content.find("Workflow-Phasen")
        assert workflow_start > 0, "Workflow-Phasen Sektion nicht gefunden"
        workflow_content = content[workflow_start:]
        idx_char = workflow_content.find(">Charaktere<")
        assert idx_char > 0, "Charaktere-Karte nicht in Workflow-Phasen gefunden"
        a_start = workflow_content.rfind("<a ", 0, idx_char)
        div_start = workflow_content.rfind("workflow-card", 0, idx_char)
        card_block = workflow_content[min(a_start, div_start) if a_start >= 0 else div_start:idx_char]
        assert "onclick" in card_block or "href=" in card_block, (
            "Charaktere-Workflow-Karte hat weder onclick noch href — "
            "cursor:pointer ohne Handler = toter Klick"
        )

    def test_should_have_weltenbau_onclick(self):
        """AK-18: Workflow-Karte 'Weltenbau' ist klickbar (via <a> oder onclick)."""
        r = self.client.get(self.url)
        content = r.content.decode()
        workflow_start = content.find("Workflow-Phasen")
        assert workflow_start > 0, "Workflow-Phasen Sektion nicht gefunden"
        workflow_content = content[workflow_start:]
        idx_welt = workflow_content.find(">Weltenbau<")
        assert idx_welt > 0, "Weltenbau-Karte nicht in Workflow-Phasen gefunden"
        a_start = workflow_content.rfind("<a ", 0, idx_welt)
        div_start = workflow_content.rfind("workflow-card", 0, idx_welt)
        card_block = workflow_content[min(a_start, div_start) if a_start >= 0 else div_start:idx_welt]
        assert "onclick" in card_block or "href=" in card_block, (
            "Weltenbau-Workflow-Karte hat weder onclick noch href — "
            "cursor:pointer ohne Handler = toter Klick"
        )

    # ── Robustheit: ALLE Workflow-Karten müssen onclick haben ────

    def test_should_have_onclick_on_all_workflow_cards(self):
        """Regression: Jede workflow-card mit cursor:pointer MUSS onclick haben."""
        import re
        r = self.client.get(self.url)
        content = r.content.decode()
        # Finde alle workflow-card divs
        pattern = r'class="card h-100 workflow-card"[^>]*>'
        cards = list(re.finditer(pattern, content))
        assert len(cards) >= 8, f"Erwartet ≥8 Workflow-Karten, gefunden: {len(cards)}"
        for match in cards:
            card_html = match.group()
            if "cursor:pointer" in card_html:
                assert "onclick" in card_html or "data-bs-toggle" in card_html, (
                    f"Workflow-Karte mit cursor:pointer aber ohne onclick/modal: "
                    f"{card_html[:120]}..."
                )

    # ── Auth: Login required ──────────────────────────────────────

    def test_should_require_login(self):
        """E-1: Nicht eingeloggt → Redirect zu Login."""
        from django.test import Client
        anon = Client(SERVER_NAME="writing.iil.pet")
        r = anon.get(self.url)
        assert r.status_code in (302, 400)
