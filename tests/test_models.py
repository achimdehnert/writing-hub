import uuid

import pytest
from django.contrib.auth.models import User

from apps.projects.models import BookProject
from apps.series.models import BookSeries
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

    def test_book_project_with_lookup_fields(self):
        from apps.projects.models import ContentTypeLookup, GenreLookup, AudienceLookup
        ct = ContentTypeLookup.objects.create(name="Roman", order=1)
        genre = GenreLookup.objects.create(name="Fantasy", order=1)
        audience = AudienceLookup.objects.create(name="Erwachsene", order=1)
        project = BookProject.objects.create(
            title="Fantasy Roman",
            owner=self.user,
            content_type_lookup=ct,
            genre_lookup=genre,
            audience_lookup=audience,
        )
        assert project.content_type_lookup == ct
        assert project.genre_lookup == genre
        assert project.audience_lookup == audience

    def test_book_project_with_series(self):
        series = BookSeries.objects.create(title="Meine Serie", owner=self.user)
        project = BookProject.objects.create(
            title="Band 1",
            owner=self.user,
            series=series,
        )
        assert project.series == series
        assert str(series) == "Meine Serie"

    def test_book_project_series_nullable(self):
        project = BookProject.objects.create(
            title="Einzelband",
            owner=self.user,
        )
        assert project.series is None


@pytest.mark.django_db
class TestBookSeriesModel:
    def setup_method(self):
        self.user = User.objects.create_user(username="seriesuser", password="pass123")

    def test_create_series(self):
        series = BookSeries.objects.create(
            title="Die Chroniken",
            owner=self.user,
            genre="Fantasy",
        )
        assert series.pk is not None
        assert str(series) == "Die Chroniken"

    def test_series_owner_filter(self):
        other = User.objects.create_user(username="otherseriesuser", password="pass123")
        BookSeries.objects.create(title="Mine", owner=self.user)
        BookSeries.objects.create(title="Theirs", owner=other)
        assert BookSeries.objects.filter(owner=self.user).count() == 1

    def test_series_delete_nullifies_project_series(self):
        series = BookSeries.objects.create(title="Temporäre Serie", owner=self.user)
        project = BookProject.objects.create(
            title="Projekt in Serie",
            owner=self.user,
            series=series,
        )
        series.delete()
        project.refresh_from_db()
        assert project.series is None


@pytest.mark.django_db
class TestProjectWorldLinkModel:
    def setup_method(self):
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
        ProjectWorldLink.objects.create(
            project=self.project,
            weltenhub_world_id=uuid.uuid4(),
        )
        project_pk = self.project.pk
        self.project.delete()
        assert ProjectWorldLink.objects.filter(project_id=project_pk).count() == 0
