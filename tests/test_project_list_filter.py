import pytest
from django.contrib.auth.models import User
from django.test import Client

from apps.projects.models import BookProject, ContentTypeLookup, GenreLookup
from apps.series.models import BookSeries


@pytest.mark.django_db
class TestProjectListFilter:
    def setup_method(self):
        self.user = User.objects.create_user(
            username="filteruser", password="pass123"
        )
        self.client = Client()
        self.client.login(username="filteruser", password="pass123")

        self.ct_roman, _ = ContentTypeLookup.objects.get_or_create(
            slug="roman", defaults={"name": "Roman", "order": 1}
        )
        self.ct_story, _ = ContentTypeLookup.objects.get_or_create(
            slug="kurzgeschichte",
            defaults={"name": "Kurzgeschichte", "order": 2},
        )
        self.genre_fantasy, _ = GenreLookup.objects.get_or_create(
            name="Fantasy", defaults={"order": 1}
        )
        self.genre_krimi, _ = GenreLookup.objects.get_or_create(
            name="Krimi", defaults={"order": 2}
        )
        self.series = BookSeries.objects.create(
            title="Meine Serie", owner=self.user
        )

        self.p1 = BookProject.objects.create(
            title="Fantasy Roman",
            owner=self.user,
            content_type_lookup=self.ct_roman,
            genre_lookup=self.genre_fantasy,
            series=self.series,
        )
        self.p2 = BookProject.objects.create(
            title="Krimi Story",
            owner=self.user,
            content_type_lookup=self.ct_story,
            genre_lookup=self.genre_krimi,
        )
        self.p3 = BookProject.objects.create(
            title="Fantasy Story",
            owner=self.user,
            content_type_lookup=self.ct_story,
            genre_lookup=self.genre_fantasy,
        )

    def test_list_no_filter_returns_all(self):
        response = self.client.get("/projekte/")
        assert response.status_code == 200
        projects = list(response.context["projects"])
        assert len(projects) == 3

    def test_filter_by_genre(self):
        response = self.client.get(
            f"/projekte/?genre={self.genre_fantasy.pk}"
        )
        assert response.status_code == 200
        titles = [p.title for p in response.context["projects"]]
        assert "Fantasy Roman" in titles
        assert "Fantasy Story" in titles
        assert "Krimi Story" not in titles

    def test_filter_by_content_type(self):
        response = self.client.get(
            f"/projekte/?typ={self.ct_story.pk}"
        )
        assert response.status_code == 200
        titles = [p.title for p in response.context["projects"]]
        assert "Krimi Story" in titles
        assert "Fantasy Story" in titles
        assert "Fantasy Roman" not in titles

    def test_filter_by_series(self):
        response = self.client.get(
            f"/projekte/?serie={self.series.pk}"
        )
        assert response.status_code == 200
        titles = [p.title for p in response.context["projects"]]
        assert "Fantasy Roman" in titles
        assert len(titles) == 1

    def test_filter_series_none(self):
        response = self.client.get("/projekte/?serie=none")
        assert response.status_code == 200
        titles = [p.title for p in response.context["projects"]]
        assert "Krimi Story" in titles
        assert "Fantasy Story" in titles
        assert "Fantasy Roman" not in titles

    def test_filter_by_title_search(self):
        response = self.client.get("/projekte/?q=fantasy")
        assert response.status_code == 200
        titles = [p.title for p in response.context["projects"]]
        assert "Fantasy Roman" in titles
        assert "Fantasy Story" in titles
        assert "Krimi Story" not in titles

    def test_filter_combined_genre_and_type(self):
        response = self.client.get(
            f"/projekte/?genre={self.genre_fantasy.pk}&typ={self.ct_story.pk}"
        )
        assert response.status_code == 200
        titles = [p.title for p in response.context["projects"]]
        assert "Fantasy Story" in titles
        assert "Fantasy Roman" not in titles
        assert "Krimi Story" not in titles

    def test_filter_context_has_options(self):
        response = self.client.get("/projekte/")
        assert "genre_options" in response.context
        assert "ct_options" in response.context
        assert "series_options" in response.context

    def test_filter_only_shows_own_series(self):
        other = User.objects.create_user(
            username="otherfilteruser", password="pass123"
        )
        BookSeries.objects.create(title="Fremde Serie", owner=other)
        response = self.client.get("/projekte/")
        series_titles = [
            s.title for s in response.context["series_options"]
        ]
        assert "Meine Serie" in series_titles
        assert "Fremde Serie" not in series_titles
