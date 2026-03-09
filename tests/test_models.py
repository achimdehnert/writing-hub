import pytest
from django.contrib.auth.models import User

from apps.projects.models import BookProject
from apps.worlds.models import ProjectWorldLink


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
        assert project.title == "Test Novel"
        assert project.owner == self.user

    def test_book_project_str_contains_title(self):
        project = BookProject.objects.create(
            title="My Book",
            owner=self.user,
        )
        assert "My Book" in str(project)

    def test_book_project_owner_filter(self):
        other = User.objects.create_user(username="otheruser", password="pass123")
        BookProject.objects.create(title="Mine", owner=self.user)
        BookProject.objects.create(title="Theirs", owner=other)
        assert BookProject.objects.filter(owner=self.user).count() == 1


@pytest.mark.django_db
class TestProjectWorldLinkModel:
    def setup_method(self):
        import uuid
        self.user = User.objects.create_user(username="worldlinkuser", password="pass123")
        self.project = BookProject.objects.create(title="Linked Project", owner=self.user)
        self.world_id = uuid.uuid4()

    def test_create_project_world_link(self):
        link = ProjectWorldLink.objects.create(
            project=self.project,
            weltenhub_world_id=self.world_id,
        )
        assert link.pk is not None
        assert link.weltenhub_world_id == self.world_id
        assert link.project == self.project

    def test_link_cascade_delete_with_project(self):
        import uuid
        ProjectWorldLink.objects.create(
            project=self.project,
            weltenhub_world_id=uuid.uuid4(),
        )
        project_pk = self.project.pk
        self.project.delete()
        assert ProjectWorldLink.objects.filter(project_id=project_pk).count() == 0
