"""Tests for ChapterContext.load_research_context() — Issue #8 Phase 3."""

import uuid

import pytest
from django.contrib.auth.models import User

from apps.authoring.handlers.chapter_writer_handler import ChapterContext


@pytest.mark.django_db
class TestLoadResearchContext:
    """Verify load_research_context loads notes + citations into research_notes."""

    def setup_method(self):
        from apps.projects.models import BookProject, OutlineVersion

        self.user = User.objects.create_user(username="ctx_user", password="pass123")
        self.project = BookProject.objects.create(
            title="Test Project", owner=self.user
        )
        self.version = OutlineVersion.objects.create(
            project=self.project,
            created_by=self.user,
            name="v1",
            is_active=True,
        )

    def _create_node(self, title="Chapter 1", notes=""):
        from apps.projects.models import OutlineNode

        return OutlineNode.objects.create(
            outline_version=self.version,
            title=title,
            beat_type="chapter",
            order=1,
            notes=notes,
        )

    def _create_citation(self, node, title="Paper A", doi="10.1234/test", year=2025):
        from apps.projects.models import ProjectCitation

        return ProjectCitation.objects.create(
            project=self.project,
            node=node,
            title=title,
            authors_json=[{"family": "Smith", "given": "J"}],
            year=year,
            doi=doi,
        )

    def test_should_load_empty_when_node_not_found(self):
        ctx = ChapterContext(
            project_id=str(self.project.pk),
            chapter_ref=str(uuid.uuid4()),
        )
        ctx.load_research_context()
        assert ctx.research_notes == ""

    def test_should_load_node_notes(self):
        node = self._create_node(notes="Some research notes")
        ctx = ChapterContext(
            project_id=str(self.project.pk),
            chapter_ref=str(node.pk),
        )
        ctx.load_research_context()
        assert "Some research notes" in ctx.research_notes

    def test_should_load_citations_into_research_notes(self):
        node = self._create_node()
        self._create_citation(node, title="Deep Learning Survey", doi="10.1234/dl")
        ctx = ChapterContext(
            project_id=str(self.project.pk),
            chapter_ref=str(node.pk),
        )
        ctx.load_research_context()
        assert "Deep Learning Survey" in ctx.research_notes
        assert "10.1234/dl" in ctx.research_notes
        assert "Zugeordnete Quellen" in ctx.research_notes

    def test_should_combine_citations_and_notes(self):
        node = self._create_node(notes="Manual research notes here")
        self._create_citation(node, title="Paper B", doi="10.5678/b")
        ctx = ChapterContext(
            project_id=str(self.project.pk),
            chapter_ref=str(node.pk),
        )
        ctx.load_research_context()
        assert "Paper B" in ctx.research_notes
        assert "Manual research notes here" in ctx.research_notes
        # Citations should come before manual notes
        cit_pos = ctx.research_notes.index("Paper B")
        notes_pos = ctx.research_notes.index("Manual research notes here")
        assert cit_pos < notes_pos

    def test_should_handle_no_citations_gracefully(self):
        node = self._create_node(notes="Only notes, no citations")
        ctx = ChapterContext(
            project_id=str(self.project.pk),
            chapter_ref=str(node.pk),
        )
        ctx.load_research_context()
        assert ctx.research_notes == "Only notes, no citations"
