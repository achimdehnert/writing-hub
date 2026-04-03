import pytest
from django.contrib.auth.models import User
from django.test import Client


@pytest.mark.django_db
class TestAuthRedirects:
    def test_root_redirects_to_projects(self):
        client = Client()
        response = client.get("/")
        assert response.status_code in (301, 302)
        assert "/projects/" in response["Location"]

    def test_projects_list_requires_login(self):
        client = Client()
        response = client.get("/projects/")
        assert response.status_code in (301, 302)
        assert "/accounts/login" in response["Location"]

    def test_projects_list_accessible_when_logged_in(self):
        User.objects.create_user(username="testuser", password="testpass123")
        client = Client()
        client.login(username="testuser", password="testpass123")
        response = client.get("/projects/")
        assert response.status_code == 200

    def test_login_page_accessible(self):
        client = Client()
        response = client.get("/accounts/login/")
        assert response.status_code == 200
