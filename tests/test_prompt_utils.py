"""
Tests for apps.core.prompt_utils — promptfw integration.
"""


class TestRenderPrompt:
    """Test render_prompt function."""

    def test_render_prompt_returns_messages_list(self):
        """render_prompt should return a list of message dicts."""
        from apps.core.prompt_utils import render_prompt

        messages = render_prompt(
            "idea_import/brainstorm_ideas",
            inspiration="Test inspiration",
            genre="Thriller",
            style_hint="",
            count=3,
        )

        assert isinstance(messages, list)
        if messages:  # May be empty if promptfw not installed
            assert all(isinstance(m, dict) for m in messages)
            assert all("role" in m and "content" in m for m in messages)

    def test_render_prompt_nonexistent_template_raises(self):
        """render_prompt should raise PromptRenderError for nonexistent template."""
        import pytest
        from apps.core.prompt_utils import PromptRenderError, render_prompt

        with pytest.raises(PromptRenderError):
            render_prompt("nonexistent/template", foo="bar")

    def test_prompt_exists_returns_true_for_existing(self):
        """prompt_exists should return True for existing templates."""
        from apps.core.prompt_utils import prompt_exists

        assert prompt_exists("idea_import/brainstorm_ideas") is True
        assert prompt_exists("authors/analyze_style") is True
        assert prompt_exists("outlines/structure_pass") is True

    def test_prompt_exists_returns_false_for_nonexistent(self):
        """prompt_exists should return False for nonexistent templates."""
        from apps.core.prompt_utils import prompt_exists

        assert prompt_exists("nonexistent/template") is False
        assert prompt_exists("foo/bar/baz") is False


class TestPromptTemplatesExist:
    """Verify all expected prompt templates exist."""

    EXPECTED_TEMPLATES = [
        "idea_import/brainstorm_ideas",
        "idea_import/brainstorm_topics",
        "idea_import/refine_idea",
        "idea_import/refine_topic",
        "idea_import/generate_expose",
        "idea_import/generate_premise",
        "outlines/structure_pass",
        "outlines/detail_pass",
        "outlines/enrich_node",
        "authors/analyze_style",
        "authors/extract_rules",
        "authors/generate_sample",
        "projects/review_lector",
        "projects/review_dramaturg",
        "projects/review_genre_expert",
        "projects/review_story_editor",
        "projects/review_beta_reader",
        "projects/lektorat_analyze",
        "projects/generate_keywords",
        "projects/marketing_blurb",
    ]

    def test_all_expected_templates_exist(self):
        """All expected prompt templates should exist."""
        from apps.core.prompt_utils import prompt_exists

        missing = [t for t in self.EXPECTED_TEMPLATES if not prompt_exists(t)]
        assert missing == [], f"Missing templates: {missing}"

    def test_templates_have_valid_structure(self):
        """Templates should have system and user sections."""
        from apps.core.prompt_utils import PROMPTS_DIR

        for template_name in self.EXPECTED_TEMPLATES:
            template_path = PROMPTS_DIR / f"{template_name}.jinja2"
            if template_path.exists():
                content = template_path.read_text()
                assert "system:" in content, f"{template_name} missing system section"
                assert "user:" in content, f"{template_name} missing user section"
