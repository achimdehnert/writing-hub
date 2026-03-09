import pytest
from django.contrib.auth.models import User

from apps.projects.models import BookProject
from apps.worlds.models import World


@pytest.mark.django_db
class TestBookProjectModel:
    def setup_method(self):
        self.user = User.objects.create_user(username="modeluser", password="pass123")

    def test_create_book_project(self):
        project = BookProject.objects.create(
            title="Test Novel",
            owner=self.user,
        )
        assert project.pk is not None
        assert str(project.title) == "Test Novel"
        assert project.owner == self.user

    def test_book_project_str(self):
        project = BookProject.objects.create(
            title="My Book",
            owner=self.user,
        )
        assert "My Book" in str(project)


@pytest.mark.django_db
class TestWorldModel:
    def setup_method(self):
        self.user = User.objects.create_user(username="worldmodeluser", password="pass123")

    def test_create_world(self):
        world = World.objects.create(
            name="Middle Earth",
            owner=self.user,
        )
        assert world.pk is not None
        assert world.name == "Middle Earth"

    def test_world_str(self):
        world = World.objects.create(
            name="Narnia",
            owner=self.user,
        )
        assert "Narnia" in str(world)
