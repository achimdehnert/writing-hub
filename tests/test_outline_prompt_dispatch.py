"""
Tests for outline prompt dispatch — DB-backed, content-type-aware templates.

Covers:
  - Content-type → group mapping
  - DB template resolution (active version)
  - File fallback when no DB template exists
  - Version management (activate/deactivate)
  - Quality rating model
  - Template rendering with Jinja2 variables
  - Template stats aggregation
"""
import pytest
from unittest.mock import MagicMock, patch

from apps.outlines.models import (
    CONTENT_TYPE_TO_GROUP,
    OutlinePromptTemplate,
    OutlineQualityRating,
    get_content_type_group,
)


# ── Content-Type Mapping ────────────────────────────────────────────

class TestContentTypeGroupMapping:
    """Test content_type → group mapping logic."""

    def test_should_map_novel_to_fiction(self):
        assert get_content_type_group("novel") == "fiction"

    def test_should_map_short_story_to_fiction(self):
        assert get_content_type_group("short_story") == "fiction"

    def test_should_map_screenplay_to_fiction(self):
        assert get_content_type_group("screenplay") == "fiction"

    def test_should_map_academic_to_academic(self):
        assert get_content_type_group("academic") == "academic"

    def test_should_map_scientific_to_academic(self):
        assert get_content_type_group("scientific") == "academic"

    def test_should_map_essay_to_nonfiction(self):
        assert get_content_type_group("essay") == "nonfiction"

    def test_should_map_nonfiction_to_nonfiction(self):
        assert get_content_type_group("nonfiction") == "nonfiction"

    def test_should_default_to_fiction_for_unknown(self):
        assert get_content_type_group("unknown_type") == "fiction"

    def test_should_cover_all_book_project_content_types(self):
        """Every BookProject.ContentType choice must be in the mapping."""
        from apps.projects.models import BookProject

        for choice_value, _label in BookProject.ContentType.choices:
            group = get_content_type_group(choice_value)
            assert group in ("fiction", "academic", "nonfiction"), (
                f"Unmapped content_type: {choice_value}"
            )


# ── OutlinePromptTemplate Model ─────────────────────────────────────

@pytest.mark.django_db
class TestOutlinePromptTemplateModel:
    """Test OutlinePromptTemplate CRUD and versioning."""

    def test_should_create_template_with_version_1(self):
        tpl = OutlinePromptTemplate.objects.create(
            content_type_group="academic",
            template_key="enrich_node",
            system_prompt="Du bist ein Lektor.",
            user_prompt_template="Abschnitt {{ order }}: {{ title }}",
            is_active=True,
        )
        assert tpl.version == 1
        assert tpl.is_active is True

    def test_should_auto_increment_version(self):
        OutlinePromptTemplate.objects.create(
            content_type_group="fiction",
            template_key="enrich_node",
            system_prompt="v1",
            user_prompt_template="v1",
            version=1,
        )
        tpl2 = OutlinePromptTemplate(
            content_type_group="fiction",
            template_key="enrich_node",
            system_prompt="v2",
            user_prompt_template="v2",
        )
        tpl2.version = 0  # trigger auto-increment
        tpl2.save()
        assert tpl2.version == 2

    def test_should_enforce_unique_active_per_key(self):
        """Only one template per (group, key) can be active."""
        tpl1 = OutlinePromptTemplate.objects.create(
            content_type_group="academic",
            template_key="detail_pass",
            system_prompt="v1",
            user_prompt_template="v1",
            version=1,
            is_active=True,
        )
        tpl2 = OutlinePromptTemplate.objects.create(
            content_type_group="academic",
            template_key="detail_pass",
            system_prompt="v2",
            user_prompt_template="v2",
            version=2,
            is_active=False,
        )
        tpl2.activate()

        tpl1.refresh_from_db()
        assert tpl1.is_active is False
        assert tpl2.is_active is True

    def test_should_render_messages_with_context(self):
        tpl = OutlinePromptTemplate(
            system_prompt="Du bist ein {{ role }}.",
            user_prompt_template="Abschnitt {{ order }}: {{ title }}",
        )
        msgs = tpl.render_messages(role="Lektor", order=3, title="Methodik")
        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert msgs[0]["content"] == "Du bist ein Lektor."
        assert msgs[1]["role"] == "user"
        assert "Abschnitt 3: Methodik" in msgs[1]["content"]

    def test_should_skip_empty_prompt_in_messages(self):
        tpl = OutlinePromptTemplate(
            system_prompt="",
            user_prompt_template="Only user prompt.",
        )
        msgs = tpl.render_messages()
        assert len(msgs) == 1
        assert msgs[0]["role"] == "user"

    def test_should_have_readable_str(self):
        tpl = OutlinePromptTemplate(
            content_type_group="academic",
            template_key="enrich_node",
            version=3,
            is_active=True,
        )
        s = str(tpl)
        assert "v3" in s
        assert "✓" in s


# ── Prompt Dispatch ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestRenderOutlinePrompt:
    """Test render_outline_prompt dispatch logic."""

    def test_should_use_db_template_when_active(self):
        """DB template is preferred over file template."""
        from apps.outlines.prompt_dispatch import render_outline_prompt

        OutlinePromptTemplate.objects.create(
            content_type_group="academic",
            template_key="enrich_node",
            system_prompt="DB system prompt for academic.",
            user_prompt_template="DB user: {{ title }}",
            version=1,
            is_active=True,
        )
        msgs = render_outline_prompt(
            template_key="enrich_node",
            content_type="scientific",  # maps to "academic" group
            title="Forschungsstand",
        )
        assert any("DB system prompt" in m["content"] for m in msgs)
        assert any("Forschungsstand" in m["content"] for m in msgs)

    def test_should_fall_back_to_file_when_no_db_template(self):
        """When no DB template exists, .jinja2 file is used."""
        from apps.outlines.prompt_dispatch import render_outline_prompt

        # No DB templates → must fall back to file
        msgs = render_outline_prompt(
            template_key="enrich_node",
            content_type="novel",
            context_block="Test project",
            order=1,
            title="Kapitel 1",
        )
        # File template should render something
        assert len(msgs) >= 1
        assert any("Kapitel" in m.get("content", "") or "1" in m.get("content", "") for m in msgs)

    def test_should_dispatch_fiction_to_fiction_group(self):
        """novel content_type dispatches to fiction group template."""
        from apps.outlines.prompt_dispatch import render_outline_prompt

        OutlinePromptTemplate.objects.create(
            content_type_group="fiction",
            template_key="enrich_node",
            system_prompt="Fiction system.",
            user_prompt_template="Fiction user: {{ title }}",
            version=1,
            is_active=True,
        )
        msgs = render_outline_prompt(
            template_key="enrich_node",
            content_type="novel",
            title="Der Sturm",
        )
        assert any("Fiction system" in m["content"] for m in msgs)

    def test_should_not_use_inactive_template(self):
        """Inactive DB template is skipped, file fallback used."""
        from apps.outlines.prompt_dispatch import render_outline_prompt

        OutlinePromptTemplate.objects.create(
            content_type_group="nonfiction",
            template_key="enrich_node",
            system_prompt="Should not appear.",
            user_prompt_template="Should not appear.",
            version=1,
            is_active=False,  # inactive!
        )
        msgs = render_outline_prompt(
            template_key="enrich_node",
            content_type="essay",
            context_block="Test",
            order=1,
            title="Einleitung",
        )
        # Should NOT contain the inactive template's content
        assert not any("Should not appear" in m.get("content", "") for m in msgs)


# ── Active Template Lookup ───────────────────────────────────────────

@pytest.mark.django_db
class TestGetActiveTemplate:
    """Test get_active_template for quality feedback linking."""

    def test_should_return_active_template(self):
        from apps.outlines.prompt_dispatch import get_active_template

        tpl = OutlinePromptTemplate.objects.create(
            content_type_group="academic",
            template_key="enrich_node",
            system_prompt="test",
            user_prompt_template="test",
            version=1,
            is_active=True,
        )
        result = get_active_template("enrich_node", "scientific")
        assert result.pk == tpl.pk

    def test_should_return_none_when_no_db_template(self):
        from apps.outlines.prompt_dispatch import get_active_template

        result = get_active_template("enrich_node", "novel")
        assert result is None


# ── Quality Rating ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestOutlineQualityRating:
    """Test quality rating model and template stats."""

    @pytest.fixture
    def _setup_data(self, django_user_model):
        """Create test data for rating tests."""
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass"
        )
        from apps.projects.models import BookProject, OutlineNode, OutlineVersion

        project = BookProject.objects.create(
            title="Test", owner=user, content_type="scientific"
        )
        outline = OutlineVersion.objects.create(
            project=project, name="v1", source="academic_essay"
        )
        node = OutlineNode.objects.create(
            outline_version=outline, title="Methodik", order=1
        )
        tpl = OutlinePromptTemplate.objects.create(
            content_type_group="academic",
            template_key="enrich_node",
            system_prompt="test",
            user_prompt_template="test",
            version=1,
            is_active=True,
        )
        self.user = user
        self.node = node
        self.tpl = tpl

    def test_should_create_rating(self, _setup_data):
        rating = OutlineQualityRating.objects.create(
            outline_node=self.node,
            prompt_template=self.tpl,
            rating=4,
            feedback="Gute Struktur, aber Methodik fehlt.",
            created_by=self.user,
        )
        assert rating.rating == 4
        assert "Gut" in rating.get_rating_display()

    def test_should_link_rating_to_template_version(self, _setup_data):
        OutlineQualityRating.objects.create(
            outline_node=self.node,
            prompt_template=self.tpl,
            rating=3,
            created_by=self.user,
        )
        assert self.tpl.ratings.count() == 1

    def test_should_compute_template_stats(self, _setup_data):
        from apps.outlines.prompt_dispatch import get_template_stats

        OutlineQualityRating.objects.create(
            outline_node=self.node,
            prompt_template=self.tpl,
            rating=4,
            created_by=self.user,
        )
        OutlineQualityRating.objects.create(
            outline_node=self.node,
            prompt_template=self.tpl,
            rating=2,
            created_by=self.user,
        )
        stats = get_template_stats("academic")
        assert len(stats["templates"]) == 1
        t = stats["templates"][0]
        assert t["rating_count"] == 2
        assert t["avg_rating"] == 3.0


# ── Seed Data ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSeedData:
    """Test that seed migration creates expected templates."""

    def test_should_have_6_seed_templates_after_migration(self):
        """Migration 0002 creates 3 groups × 2 keys = 6 templates."""
        count = OutlinePromptTemplate.objects.count()
        assert count == 6, f"Expected 6 seed templates, got {count}"

    def test_should_have_active_template_for_each_group_and_key(self):
        for group in ("fiction", "academic", "nonfiction"):
            for key in ("enrich_node", "detail_pass"):
                exists = OutlinePromptTemplate.objects.filter(
                    content_type_group=group,
                    template_key=key,
                    is_active=True,
                ).exists()
                assert exists, f"Missing active template for {group}/{key}"

    def test_academic_enrich_should_mention_forschungsfrage(self):
        tpl = OutlinePromptTemplate.objects.get(
            content_type_group="academic",
            template_key="enrich_node",
            is_active=True,
        )
        assert "Forschungsfrage" in tpl.user_prompt_template
        assert "Szenen" not in tpl.user_prompt_template

    def test_fiction_enrich_should_mention_szenen(self):
        tpl = OutlinePromptTemplate.objects.get(
            content_type_group="fiction",
            template_key="enrich_node",
            is_active=True,
        )
        assert "Szenen" in tpl.user_prompt_template
        assert "Forschungsfrage" not in tpl.user_prompt_template

    def test_nonfiction_enrich_should_mention_kernaussage(self):
        tpl = OutlinePromptTemplate.objects.get(
            content_type_group="nonfiction",
            template_key="enrich_node",
            is_active=True,
        )
        assert "Kernaussage" in tpl.user_prompt_template
        assert "Szenen" not in tpl.user_prompt_template
