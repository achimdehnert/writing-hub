import pytest
from django.contrib.auth.models import User
from django.test import Client

from apps.series.models import BookSeries


@pytest.mark.django_db
class TestSeriesHTMLViews:
    def setup_method(self):
        self.user = User.objects.create_user(username="seriesviewuser", password="pass123")
        self.client = Client()
        self.client.login(username="seriesviewuser", password="pass123")

    def test_series_list_requires_login(self):
        anon = Client()
        response = anon.get("/serien/")
        assert response.status_code in (301, 302)
        assert "/accounts/login" in response["Location"]

    def test_series_list_accessible_logged_in(self):
        response = self.client.get("/serien/")
        assert response.status_code == 200

    def test_series_list_empty_state(self):
        response = self.client.get("/serien/")
        assert response.status_code == 200
        assert b"Noch keine Serien" in response.content

    def test_series_create_get(self):
        response = self.client.get("/serien/neu/")
        assert response.status_code == 200

    def test_series_create_post(self):
        response = self.client.post(
            "/serien/neu/",
            {
                "title": "Meine Testserie",
                "genre": "Fantasy",
                "description": "Eine Testserie",
            },
        )
        assert response.status_code in (301, 302)
        assert BookSeries.objects.filter(title="Meine Testserie", owner=self.user).exists()

    def test_series_edit_get(self):
        series = BookSeries.objects.create(title="Edit Me", owner=self.user)
        response = self.client.get(f"/serien/{series.pk}/bearbeiten/")
        assert response.status_code == 200

    def test_series_edit_post(self):
        series = BookSeries.objects.create(title="Original", owner=self.user)
        response = self.client.post(
            f"/serien/{series.pk}/bearbeiten/",
            {"title": "Geändert", "genre": "", "description": ""},
        )
        assert response.status_code in (301, 302)
        series.refresh_from_db()
        assert series.title == "Geändert"

    def test_series_delete_get(self):
        series = BookSeries.objects.create(title="Delete Me", owner=self.user)
        response = self.client.get(f"/serien/{series.pk}/loeschen/")
        assert response.status_code == 200

    def test_series_delete_post(self):
        series = BookSeries.objects.create(title="Gone", owner=self.user)
        pk = series.pk
        response = self.client.post(f"/serien/{pk}/loeschen/")
        assert response.status_code in (301, 302)
        assert not BookSeries.objects.filter(pk=pk).exists()

    def test_other_user_cannot_edit_series(self):
        other = User.objects.create_user(username="otheruser2", password="pass123")
        series = BookSeries.objects.create(title="Not Mine", owner=other)
        response = self.client.get(f"/serien/{series.pk}/bearbeiten/")
        assert response.status_code == 404

    def test_other_user_cannot_delete_series(self):
        other = User.objects.create_user(username="otheruser3", password="pass123")
        series = BookSeries.objects.create(title="Not Mine Either", owner=other)
        response = self.client.post(f"/serien/{series.pk}/loeschen/")
        assert response.status_code == 404
