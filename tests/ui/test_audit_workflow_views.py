"""
REFLEX Zirkel 2 — UI Audit: Workflow-Views erreichbar (UC-003 Ergänzung)

Stellt sicher, dass alle Workflow-Phasen-Links von der Projekt-Detailseite
tatsächlich HTTP 200 liefern (keine toten Links).
"""
import pytest
from django.urls import reverse


def _seed_project(db):
    """Erzeugt ein Testprojekt mit Outline."""
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
            title="Workflow-Test Projekt",
            owner=user,
            content_type="novel",
            genre="Thriller",
            target_word_count=50000,
            description="Testprojekt für Workflow-Views.",
        )
    version = OutlineVersion.objects.filter(project=project, is_active=True).first()
    if not version:
        version = OutlineVersion.objects.create(
            project=project, name="Test", is_active=True, source="three_act",
        )
        OutlineNode.objects.create(
            outline_version=version, title="Kapitel 1",
            order=1, beat_type="chapter", word_count=500,
        )
    return project


@pytest.mark.django_db
class TestWorkflowViewsReachable:
    """Alle Workflow-Views von der Detailseite müssen HTTP 200 liefern."""

    @pytest.fixture(autouse=True)
    def setup(self, db, auth_client):
        self.project = _seed_project(db)
        self.client = auth_client

    def test_should_reach_lektorat(self):
        url = reverse("projects:lektorat", kwargs={"pk": self.project.pk})
        assert self.client.get(url).status_code == 200

    def test_should_reach_review(self):
        url = reverse("projects:review", kwargs={"pk": self.project.pk})
        assert self.client.get(url).status_code == 200

    def test_should_reach_publishing(self):
        url = reverse("projects:publishing", kwargs={"pk": self.project.pk})
        assert self.client.get(url).status_code == 200

    def test_should_reach_export(self):
        url = reverse("projects:export", kwargs={"pk": self.project.pk})
        assert self.client.get(url).status_code == 200

    def test_should_reach_manuscript(self):
        url = reverse("projects:manuscript", kwargs={"pk": self.project.pk})
        assert self.client.get(url).status_code == 200

    def test_should_reach_health(self):
        url = reverse("projects:health", kwargs={"pk": self.project.pk})
        assert self.client.get(url).status_code == 200

    def test_should_reach_analysis(self):
        url = reverse("projects:analysis", kwargs={"pk": self.project.pk})
        assert self.client.get(url).status_code == 200

    def test_should_reach_drama(self):
        url = reverse("projects:drama_dashboard", kwargs={"pk": self.project.pk})
        assert self.client.get(url).status_code == 200

    def test_should_reach_pitch(self):
        url = reverse("projects:pitch_dashboard", kwargs={"pk": self.project.pk})
        assert self.client.get(url).status_code == 200

    def test_should_reach_budget(self):
        url = reverse("projects:budget", kwargs={"pk": self.project.pk})
        assert self.client.get(url).status_code == 200

    def test_should_reach_chapter_writer(self):
        url = reverse("projects:chapter_writer", kwargs={"pk": self.project.pk})
        assert self.client.get(url).status_code == 200

    def test_should_reach_citations(self):
        url = reverse("projects:citations", kwargs={"pk": self.project.pk})
        assert self.client.get(url).status_code == 200

    def test_should_reach_research(self):
        url = reverse("projects:research_dashboard", kwargs={"pk": self.project.pk})
        assert self.client.get(url).status_code == 200

    def test_should_reach_beta(self):
        url = reverse("projects:beta_dashboard", kwargs={"pk": self.project.pk})
        assert self.client.get(url).status_code == 200

    def test_should_reach_edit(self):
        url = reverse("projects:edit", kwargs={"pk": self.project.pk})
        assert self.client.get(url).status_code == 200

    def test_should_reach_versions(self):
        url = reverse("projects:versions", kwargs={"pk": self.project.pk})
        assert self.client.get(url).status_code == 200
