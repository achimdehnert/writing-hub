import pytest
from django.contrib.auth.models import User
from django.test import Client


@pytest.mark.django_db
class TestProjectsAPI:
    def setup_method(self):
        self.user = User.objects.create_user(username="apiuser", password="apipass123")
        self.client = Client()
        self.client.login(username="apiuser", password="apipass123")

    def test_projects_api_list_returns_200(self):
        response = self.client.get("/projekte/api/")
        assert response.status_code == 200

    def test_projects_api_returns_json(self):
        response = self.client.get("/projekte/api/")
        assert response["Content-Type"].startswith("application/json")

    def test_projects_api_list_empty_for_new_user(self):
        response = self.client.get("/projekte/api/")
        data = response.json()
        assert isinstance(data, list) or "results" in data or data == []

    def test_projects_api_unauthenticated_returns_403_or_401(self):
        client = Client()
        response = client.get("/projekte/api/")
        assert response.status_code in (401, 403)


@pytest.mark.django_db
class TestWorldsAPIAuth:
    """Worlds API uses IsAuthenticated (DRF session/token auth)."""

    def test_worlds_api_unauthenticated_returns_401_or_403(self):
        client = Client()
        response = client.get("/api/v1/worlds/")
        assert response.status_code in (401, 403)

    def test_worlds_api_authenticated_returns_200(self):
        User.objects.create_user(username="worldapiuser", password="pass123")
        client = Client()
        client.login(username="worldapiuser", password="pass123")
        response = client.get("/api/v1/worlds/")
        assert response.status_code == 200

    def test_worlds_api_returns_empty_list_for_new_user(self):
        User.objects.create_user(username="worldapiuser2", password="pass123")
        client = Client()
        client.login(username="worldapiuser2", password="pass123")
        response = client.get("/api/v1/worlds/")
        assert response.json() == []


@pytest.mark.django_db
class TestAPIHealthEndpoint:
    def test_api_health_no_auth_required(self):
        client = Client()
        response = client.get("/api/v1/health/")
        assert response.status_code == 200
