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
        response = self.client.get("/projects/api/")
        assert response.status_code == 200

    def test_projects_api_returns_json(self):
        response = self.client.get("/projects/api/")
        assert response["Content-Type"].startswith("application/json")

    def test_projects_api_unauthenticated_returns_403_or_401(self):
        client = Client()
        response = client.get("/projects/api/")
        assert response.status_code in (401, 403)


@pytest.mark.django_db
class TestWorldsAPI:
    def setup_method(self):
        self.user = User.objects.create_user(username="worlduser", password="worldpass123")
        self.client = Client()
        self.client.login(username="worlduser", password="worldpass123")

    def test_worlds_api_list_returns_200(self):
        response = self.client.get("/api/v1/worlds/")
        assert response.status_code == 200

    def test_worlds_api_unauthenticated_returns_403_or_401(self):
        client = Client()
        response = client.get("/api/v1/worlds/")
        assert response.status_code in (401, 403)
