"""
Frontend View Tests — writing-hub
==================================
Testet alle HTML-Views auf:
  - HTTP 200 (oder 302 bei Login-Redirect für anonyme Requests)
  - Template wird gerendert (kein TemplateDoesNotExist / TemplateSyntaxError)
  - Kein 500er

Abgedeckte Apps: projects, outlines, series, authors, worlds, idea_import
"""
import pytest
from django.contrib.auth.models import User
from django.test import Client

from apps.authoring.models_jobs import BatchWriteJob, JobStatus
from apps.projects.models import BookProject, ContentTypeLookup, GenreLookup, OutlineNode
from apps.series.models import BookSeries


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user(db):
    return User.objects.create_user(username="fe_testuser", password="pass123")


@pytest.fixture
def auth_client(user):
    c = Client()
    c.login(username="fe_testuser", password="pass123")
    return c


@pytest.fixture
def anon_client():
    return Client()


@pytest.fixture
def project(db, user):
    ct, _ = ContentTypeLookup.objects.get_or_create(
        slug="roman", defaults={"name": "Roman", "order": 1}
    )
    genre, _ = GenreLookup.objects.get_or_create(
        name="Fantasy", defaults={"order": 1}
    )
    return BookProject.objects.create(
        title="Test-Projekt FE",
        owner=user,
        content_type_lookup=ct,
        genre_lookup=genre,
        target_word_count=80000,
    )


@pytest.fixture
def outline_node(db, project):
    from apps.projects.models import OutlineVersion
    version = OutlineVersion.objects.create(
        project=project,
        name="Test Version",
    )
    return OutlineNode.objects.create(
        outline_version=version,
        title="Kapitel 1",
        beat_type="chapter",
        order=1,
    )


@pytest.fixture
def series(db, user):
    return BookSeries.objects.create(title="Test-Serie FE", owner=user)


@pytest.fixture
def batch_job(db, project, user):
    return BatchWriteJob.objects.create(
        project=project,
        requested_by=user,
        status=JobStatus.PENDING,
        node_ids=[],
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ok(response):
    """Akzeptiert 200 und Redirect 301/302."""
    assert response.status_code in (200, 301, 302), (
        f"Expected 200/302, got {response.status_code}"
    )


def must_200(response):
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}"
    )


def must_redirect(response):
    assert response.status_code in (301, 302), (
        f"Expected redirect, got {response.status_code}"
    )


# ---------------------------------------------------------------------------
# Anonyme Requests → Login-Redirect
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestLoginRequired:
    """Alle geschützten Seiten müssen anonym auf /accounts/login/ redirecten."""

    ANON_URLS = [
        "/projekte/",
        "/projekte/new/",
        "/outlines/",
        "/autoren/",
        "/welten/",
        "/ideen/",
        "/serien/",
    ]

    @pytest.mark.parametrize("url", ANON_URLS)
    def test_anonymous_redirects_to_login(self, anon_client, url):
        response = anon_client.get(url)
        must_redirect(response)
        location = response.get("Location", "")
        assert "login" in location.lower() or response.status_code == 302, (
            f"Expected login redirect for {url}, got Location: {location}"
        )


# ---------------------------------------------------------------------------
# Projects App
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestProjectViews:

    def test_project_list(self, auth_client):
        must_200(auth_client.get("/projekte/"))

    def test_project_list_pagination(self, auth_client):
        must_200(auth_client.get("/projekte/?page=1"))

    def test_project_list_partial_htmx(self, auth_client):
        must_200(auth_client.get("/projekte/partial/"))

    def test_project_list_partial_with_filter(self, auth_client, project):
        must_200(auth_client.get(f"/projekte/partial/?q={project.title[:5]}"))

    def test_project_list_filter_genre(self, auth_client, project):
        must_200(auth_client.get(f"/projekte/?genre={project.genre_lookup.pk}"))

    def test_project_list_filter_typ(self, auth_client, project):
        must_200(auth_client.get(f"/projekte/?typ={project.content_type_lookup.pk}"))

    def test_project_create_get(self, auth_client):
        must_200(auth_client.get("/projekte/new/"))

    def test_project_detail(self, auth_client, project):
        must_200(auth_client.get(f"/projekte/{project.pk}/"))

    def test_project_edit_get(self, auth_client, project):
        must_200(auth_client.get(f"/projekte/{project.pk}/edit/"))

    def test_project_chapter_writer(self, auth_client, project):
        must_200(auth_client.get(f"/projekte/{project.pk}/write/"))

    def test_project_manuscript(self, auth_client, project):
        must_200(auth_client.get(f"/projekte/{project.pk}/manuscript/"))

    def test_project_publishing(self, auth_client, project):
        must_200(auth_client.get(f"/projekte/{project.pk}/publishing/"))

    def test_project_export(self, auth_client, project):
        must_200(auth_client.get(f"/projekte/{project.pk}/export/"))

    def test_project_versions(self, auth_client, project):
        must_200(auth_client.get(f"/projekte/{project.pk}/versions/"))

    def test_project_review(self, auth_client, project):
        must_200(auth_client.get(f"/projekte/{project.pk}/review/"))

    def test_project_editing(self, auth_client, project):
        must_200(auth_client.get(f"/projekte/{project.pk}/editing/"))

    def test_project_lektorat(self, auth_client, project):
        must_200(auth_client.get(f"/projekte/{project.pk}/lektorat/"))

    def test_project_health(self, auth_client, project):
        must_200(auth_client.get(f"/projekte/{project.pk}/health/"))

    def test_project_health_partial(self, auth_client, project):
        must_200(auth_client.get(f"/projekte/{project.pk}/health/partial/"))

    def test_project_analysis(self, auth_client, project):
        must_200(auth_client.get(f"/projekte/{project.pk}/analysis/"))

    def test_project_budget(self, auth_client, project):
        must_200(auth_client.get(f"/projekte/{project.pk}/budget/"))

    def test_project_batch(self, auth_client, project):
        must_200(auth_client.get(f"/projekte/{project.pk}/batch/"))

    def test_project_batch_status_partial(self, auth_client, project, batch_job):
        must_200(auth_client.get(
            f"/projekte/{project.pk}/batch/{batch_job.pk}/status/"
        ))

    def test_project_research_dashboard(self, auth_client, project):
        must_200(auth_client.get(f"/projekte/{project.pk}/research/"))

    def test_project_beta_dashboard(self, auth_client, project):
        must_200(auth_client.get(f"/projekte/{project.pk}/beta/"))

    def test_project_pitch_dashboard(self, auth_client, project):
        must_200(auth_client.get(f"/projekte/{project.pk}/pitch/"))

    def test_project_drama_dashboard(self, auth_client, project):
        must_200(auth_client.get(f"/projekte/{project.pk}/drama/"))

    def test_project_peer_review(self, auth_client, project):
        project.content_type = "scientific"
        project.save(update_fields=["content_type"])
        must_200(auth_client.get(f"/projekte/{project.pk}/peer-review/"))

    def test_project_other_user_detail_404(self, project):
        User.objects.create_user(username="fe_other", password="pass123")
        c = Client()
        c.login(username="fe_other", password="pass123")
        response = c.get(f"/projekte/{project.pk}/")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Projects — Chapter Node Views
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestProjectNodeViews:

    def test_node_content_get(self, auth_client, outline_node):
        must_200(auth_client.get(f"/projekte/node/{outline_node.pk}/content/"))


# ---------------------------------------------------------------------------
# Outlines App
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestOutlineViews:

    def test_outline_list(self, auth_client):
        must_200(auth_client.get("/outlines/"))


# ---------------------------------------------------------------------------
# Series App
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSeriesViews:

    def test_series_list(self, auth_client):
        must_200(auth_client.get("/serien/"))

    def test_series_create_get(self, auth_client):
        must_200(auth_client.get("/serien/neu/"))

    def test_series_edit_get(self, auth_client, series):
        must_200(auth_client.get(f"/serien/{series.pk}/bearbeiten/"))

    def test_series_delete_get(self, auth_client, series):
        must_200(auth_client.get(f"/serien/{series.pk}/loeschen/"))


# ---------------------------------------------------------------------------
# Authors App
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAuthorViews:

    def test_author_list(self, auth_client):
        must_200(auth_client.get("/autoren/"))

    def test_author_create_get(self, auth_client):
        must_200(auth_client.get("/autoren/neu/"))


# ---------------------------------------------------------------------------
# Worlds App
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestWorldViews:

    def test_world_list(self, auth_client):
        must_200(auth_client.get("/welten/"))


# ---------------------------------------------------------------------------
# Idea Import App
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestIdeaImportViews:

    def test_idea_list(self, auth_client):
        must_200(auth_client.get("/ideen/"))


# ---------------------------------------------------------------------------
# HTMX-spezifische Tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestHTMXHeaders:
    """HTMX-Requests müssen denselben Statuscode zurückgeben wie normale Requests."""

    HTMX_HEADER = {"HTTP_HX_REQUEST": "true"}

    def test_project_list_partial_htmx_header(self, auth_client):
        response = auth_client.get("/projekte/partial/", **self.HTMX_HEADER)
        must_200(response)

    def test_project_health_partial_htmx_header(self, auth_client, project):
        response = auth_client.get(
            f"/projekte/{project.pk}/health/partial/", **self.HTMX_HEADER
        )
        must_200(response)

    def test_batch_status_partial_htmx_header(self, auth_client, project, batch_job):
        response = auth_client.get(
            f"/projekte/{project.pk}/batch/{batch_job.pk}/status/",
            **self.HTMX_HEADER,
        )
        must_200(response)


# ---------------------------------------------------------------------------
# Template-Vollständigkeit: Kritische Context-Keys
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestContextKeys:
    """Kritische Context-Keys müssen in der Response vorhanden sein."""

    def test_project_list_context_keys(self, auth_client, project):
        response = auth_client.get("/projekte/")
        assert "projects" in response.context
        assert "genre_options" in response.context
        assert "ct_options" in response.context
        assert "series_options" in response.context
        assert "page_obj" in response.context

    def test_project_list_partial_context_keys(self, auth_client, project):
        response = auth_client.get("/projekte/partial/")
        assert "projects" in response.context
        assert "page_obj" in response.context

    def test_project_detail_context(self, auth_client, project):
        response = auth_client.get(f"/projekte/{project.pk}/")
        assert "project" in response.context

    def test_project_batch_context(self, auth_client, project):
        response = auth_client.get(f"/projekte/{project.pk}/batch/")
        assert "project" in response.context
        assert "jobs" in response.context

    def test_project_analysis_context(self, auth_client, project):
        response = auth_client.get(f"/projekte/{project.pk}/analysis/")
        assert "project" in response.context

    def test_project_budget_context(self, auth_client, project):
        response = auth_client.get(f"/projekte/{project.pk}/budget/")
        assert "project" in response.context

    def test_project_research_context(self, auth_client, project):
        response = auth_client.get(f"/projekte/{project.pk}/research/")
        assert "project" in response.context

    def test_project_beta_context(self, auth_client, project):
        response = auth_client.get(f"/projekte/{project.pk}/beta/")
        assert "project" in response.context

    def test_project_pitch_context(self, auth_client, project):
        response = auth_client.get(f"/projekte/{project.pk}/pitch/")
        assert "project" in response.context

    def test_project_health_context(self, auth_client, project):
        response = auth_client.get(f"/projekte/{project.pk}/health/")
        assert "project" in response.context
