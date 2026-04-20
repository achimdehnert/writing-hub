"""
Sprint 1 Feature Tests — PublisherProfile, TOC Export, Rollenwechsel

Tests for:
  - UC 6.9: PublisherProfile CRUD + PublishingProfile defaults integration
  - UC 5.8: TOC in export (Markdown, Text, HTML)
  - UC 6.1a: Role workflow context on project detail
  - PublisherProfileForm validation
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from apps.projects.forms import PublisherProfileForm
from apps.projects.models import BookProject, OutlineNode, OutlineVersion, PublisherProfile


@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(username="sprint1", password="test", email="s1@test.de")


@pytest.fixture
def auth_client(user):
    c = Client(SERVER_NAME="writing.iil.pet")
    c.force_login(user)
    return c


@pytest.fixture
def project_with_chapters(user):
    project = BookProject.objects.create(
        title="Sprint1 Test Buch",
        owner=user,
        content_type="novel",
        genre="Thriller",
        target_word_count=50000,
    )
    version = OutlineVersion.objects.create(
        project=project,
        name="v1",
        is_active=True,
        source="three_act",
    )
    for i in range(1, 4):
        OutlineNode.objects.create(
            outline_version=version,
            title=f"Kapitel {i}",
            order=i,
            beat_type="chapter",
            content=f"Inhalt von Kapitel {i}. " * 50,
        )
    return project


# ── UC 6.9: PublisherProfile ──────────────────────────────────────


@pytest.mark.django_db
class TestPublisherProfileView:
    def test_should_get_publisher_profile_page(self, auth_client):
        url = reverse("projects:publisher_profile")
        resp = auth_client.get(url)
        assert resp.status_code == 200
        assert b"Verlagsprofil" in resp.content

    def test_should_create_publisher_profile(self, auth_client, user):
        url = reverse("projects:publisher_profile")
        resp = auth_client.post(
            url,
            {
                "name": "Mein Verlag",
                "imprint": "Belletristik",
                "default_language": "de",
                "default_age_rating": "12",
                "default_bisac_category": "FICTION / Literary",
                "logo_url": "",
                "website": "",
                "default_copyright_holder": "Max Mustermann",
            },
        )
        assert resp.status_code == 302
        profile = PublisherProfile.objects.get(owner=user)
        assert profile.name == "Mein Verlag"
        assert profile.default_age_rating == "12"
        assert profile.default_copyright_holder == "Max Mustermann"

    def test_should_update_existing_profile(self, auth_client, user):
        PublisherProfile.objects.create(
            owner=user,
            name="Alt",
            is_default=True,
        )
        url = reverse("projects:publisher_profile")
        auth_client.post(
            url,
            {
                "name": "Neu",
                "default_language": "en",
                "default_age_rating": "0",
                "imprint": "",
                "logo_url": "",
                "website": "",
                "default_copyright_holder": "",
                "default_bisac_category": "",
            },
        )
        profile = PublisherProfile.objects.get(owner=user)
        assert profile.name == "Neu"
        assert profile.default_language == "en"

    def test_should_reject_invalid_url(self, auth_client, user):
        url = reverse("projects:publisher_profile")
        resp = auth_client.post(
            url,
            {
                "name": "Test",
                "default_language": "de",
                "default_age_rating": "0",
                "imprint": "",
                "logo_url": "not-a-url",
                "website": "",
                "default_copyright_holder": "",
                "default_bisac_category": "",
            },
        )
        assert resp.status_code == 200  # re-renders form with errors
        assert PublisherProfile.objects.filter(owner=user).count() == 0


@pytest.mark.django_db
class TestPublisherProfileForm:
    def test_should_validate_valid_data(self):
        form = PublisherProfileForm(
            data={
                "name": "Testverlag",
                "default_language": "de",
                "default_age_rating": "0",
                "imprint": "",
                "logo_url": "",
                "website": "",
                "default_copyright_holder": "",
                "default_bisac_category": "",
            }
        )
        assert form.is_valid()

    def test_should_reject_empty_name(self):
        form = PublisherProfileForm(
            data={
                "name": "",
                "default_language": "de",
                "default_age_rating": "0",
            }
        )
        assert not form.is_valid()
        assert "name" in form.errors

    def test_should_reject_invalid_language_choice(self):
        form = PublisherProfileForm(
            data={
                "name": "Test",
                "default_language": "xx",
                "default_age_rating": "0",
            }
        )
        assert not form.is_valid()
        assert "default_language" in form.errors

    def test_should_reject_invalid_logo_url(self):
        form = PublisherProfileForm(
            data={
                "name": "Test",
                "default_language": "de",
                "default_age_rating": "0",
                "logo_url": "not-a-url",
            }
        )
        assert not form.is_valid()
        assert "logo_url" in form.errors


# ── UC 6.9 Integration: PublishingProfile Defaults ────────────────


@pytest.mark.django_db
class TestPublisherProfileDefaults:
    def test_should_use_publisher_defaults_for_new_project(self, user):
        PublisherProfile.objects.create(
            owner=user,
            name="IIL Verlag",
            default_language="en",
            default_age_rating="16",
            default_copyright_holder="IIL GmbH",
            default_bisac_category="TECH",
            is_default=True,
        )
        project = BookProject.objects.create(
            title="Test",
            owner=user,
            target_word_count=10000,
        )
        from apps.projects.views_publishing import _get_or_create_profile

        profile = _get_or_create_profile(project)
        assert profile.publisher_name == "IIL Verlag"
        assert profile.language == "en"
        assert profile.age_rating == "16"
        assert profile.copyright_holder == "IIL GmbH"


# ── UC 5.8: TOC Export ────────────────────────────────────────────


@pytest.mark.django_db
class TestTOCExport:
    def test_should_include_toc_in_markdown_export(self, auth_client, project_with_chapters):
        url = reverse("projects:export", kwargs={"pk": project_with_chapters.pk})
        resp = auth_client.post(
            url,
            {
                "format": "markdown",
                "include_toc": "on",
                "include_title_page": "on",
                "all_chapters": "on",
            },
        )
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Inhaltsverzeichnis" in content
        assert "Kapitel 1" in content
        assert "Kapitel 2" in content

    def test_should_include_toc_in_text_export(self, auth_client, project_with_chapters):
        url = reverse("projects:export", kwargs={"pk": project_with_chapters.pk})
        resp = auth_client.post(
            url,
            {
                "format": "text",
                "include_toc": "on",
                "all_chapters": "on",
            },
        )
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "INHALTSVERZEICHNIS" in content

    def test_should_include_toc_in_html_export(self, auth_client, project_with_chapters):
        url = reverse("projects:export", kwargs={"pk": project_with_chapters.pk})
        resp = auth_client.post(
            url,
            {
                "format": "html",
                "include_toc": "on",
                "all_chapters": "on",
            },
        )
        assert resp.status_code == 200
        content = resp.content.decode()
        assert 'class="toc"' in content
        assert "Kapitel 1" in content

    def test_should_skip_toc_when_not_checked(self, auth_client, project_with_chapters):
        url = reverse("projects:export", kwargs={"pk": project_with_chapters.pk})
        resp = auth_client.post(
            url,
            {
                "format": "markdown",
                "all_chapters": "on",
            },
        )
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Inhaltsverzeichnis" not in content


# ── UC 6.1a: Rollenwechsel context ────────────────────────────────


@pytest.mark.django_db
class TestRollenwechselWorkflow:
    def test_should_show_role_workflow_on_detail(self, auth_client, project_with_chapters):
        url = reverse("projects:detail", kwargs={"pk": project_with_chapters.pk})
        resp = auth_client.get(url)
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Aktuelle Rolle" in content
        assert "Autor" in content
        assert "Lektor" in content
        assert "Verleger" in content

    def test_should_show_publisher_profile_link(self, auth_client, project_with_chapters):
        url = reverse("projects:detail", kwargs={"pk": project_with_chapters.pk})
        resp = auth_client.get(url)
        content = resp.content.decode()
        assert "Verlagsprofil" in content
