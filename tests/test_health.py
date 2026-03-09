import pytest
from django.test import Client


@pytest.mark.django_db
class TestHealthEndpoints:
    def test_health_check_returns_ok(self):
        client = Client()
        response = client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "writing-hub"

    def test_healthz_alias_returns_ok(self):
        client = Client()
        response = client.get("/healthz/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_api_health_returns_ok(self):
        client = Client()
        response = client.get("/api/v1/health/")
        assert response.status_code == 200
