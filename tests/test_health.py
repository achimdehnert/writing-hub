import pytest
from django.test import Client


@pytest.mark.django_db
class TestHealthEndpoints:
    def setup_method(self):
        self.client = Client()

    def test_basic_health_returns_200(self):
        response = self.client.get("/api/v1/health/")
        assert response.status_code == 200

    def test_basic_health_returns_ok(self):
        data = self.client.get("/api/v1/health/").json()
        assert data["status"] == "ok"
        assert data["service"] == "writing-hub"

    def test_extended_health_no_auth_required(self):
        response = self.client.get("/api/v1/health/extended/")
        assert response.status_code in (200, 503)

    def test_extended_health_returns_json(self):
        response = self.client.get("/api/v1/health/extended/")
        assert response["Content-Type"].startswith("application/json")

    def test_extended_health_has_required_fields(self):
        data = self.client.get("/api/v1/health/extended/").json()
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "checks" in data

    def test_extended_health_database_check_present(self):
        data = self.client.get("/api/v1/health/extended/").json()
        assert "database" in data["checks"]
        assert "status" in data["checks"]["database"]

    def test_extended_health_migrations_check_present(self):
        data = self.client.get("/api/v1/health/extended/").json()
        assert "migrations" in data["checks"]
        assert "pending_count" in data["checks"]["migrations"]

    def test_extended_health_db_ok_in_test_env(self):
        data = self.client.get("/api/v1/health/extended/").json()
        assert data["checks"]["database"]["status"] == "ok"

    def test_extended_health_db_latency_is_number(self):
        data = self.client.get("/api/v1/health/extended/").json()
        db = data["checks"]["database"]
        if db["status"] == "ok":
            assert isinstance(db["latency_ms"], (int, float))

    def test_extended_health_no_pending_migrations_in_test(self):
        data = self.client.get("/api/v1/health/extended/").json()
        assert data["checks"]["migrations"]["pending_count"] == 0
