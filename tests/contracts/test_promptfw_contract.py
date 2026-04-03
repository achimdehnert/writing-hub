"""
Contract Tests: promptfw API (ADR-155)

These tests verify that writing-hub's assumptions about promptfw's API are correct.
SSoT: promptfw provides frontmatter rendering and JSON extraction.
writing-hub must NOT reimplement these.
"""
import inspect

import pytest


class TestFrontmatterContract:
    """Contract tests for promptfw.frontmatter module (SSoT for .jinja2 templates)."""

    def test_render_frontmatter_file_exists(self):
        """promptfw must export render_frontmatter_file."""
        from promptfw.frontmatter import render_frontmatter_file
        assert callable(render_frontmatter_file)

    def test_render_frontmatter_file_accepts_path_and_context(self):
        """render_frontmatter_file(file_path, **context) -> list[dict]."""
        from promptfw.frontmatter import render_frontmatter_file
        sig = inspect.signature(render_frontmatter_file)
        params = list(sig.parameters.keys())
        assert "file_path" in params, \
            f"render_frontmatter_file must accept 'file_path', got {params}"
        assert "context" in params or any(
            p.kind == inspect.Parameter.VAR_KEYWORD
            for p in sig.parameters.values()
        ), "render_frontmatter_file must accept **context kwargs"

    def test_render_frontmatter_string_exists(self):
        """promptfw must export render_frontmatter_string."""
        from promptfw.frontmatter import render_frontmatter_string
        assert callable(render_frontmatter_string)

    def test_render_frontmatter_string_returns_messages(self):
        """render_frontmatter_string returns list of message dicts."""
        from promptfw.frontmatter import render_frontmatter_string
        content = '---\nsystem: "Hallo {{ name }}."\nuser: "Frage."\n---\n'
        messages = render_frontmatter_string(content, name="Welt")
        assert isinstance(messages, list)
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "Hallo Welt."
        assert messages[1]["role"] == "user"

    def test_render_frontmatter_string_handles_jinja2(self):
        """Jinja2 conditionals and loops must work in frontmatter templates."""
        from promptfw.frontmatter import render_frontmatter_string
        content = '---\nuser: "{% if name %}Hi {{ name }}{% endif %}"\n---\n'
        messages = render_frontmatter_string(content, name="Test")
        assert "Hi Test" in messages[0]["content"]


class TestParsingContract:
    """Contract tests for promptfw.parsing — JSON extraction (SSoT)."""

    def test_extract_json_exists(self):
        """promptfw must export extract_json."""
        from promptfw.parsing import extract_json
        assert callable(extract_json)

    def test_extract_json_handles_markdown_fences(self):
        """extract_json must handle ```json ... ``` blocks."""
        from promptfw.parsing import extract_json
        text = '```json\n{"key": "value"}\n```'
        result = extract_json(text)
        assert result == {"key": "value"}

    def test_extract_json_handles_think_tags(self):
        """extract_json must strip <think> blocks (reasoning models)."""
        from promptfw.parsing import extract_json
        text = '<think>\nLet me reason...\n</think>\n{"verdict": "accept"}'
        result = extract_json(text)
        assert result == {"verdict": "accept"}

    def test_extract_json_list_exists(self):
        """promptfw must export extract_json_list."""
        from promptfw.parsing import extract_json_list
        assert callable(extract_json_list)

    def test_strip_reasoning_tags_exists(self):
        """promptfw must export strip_reasoning_tags."""
        from promptfw.parsing import strip_reasoning_tags
        assert callable(strip_reasoning_tags)

    def test_extract_json_returns_none_on_no_json(self):
        """extract_json must return None (not raise) when no JSON found."""
        from promptfw.parsing import extract_json
        assert extract_json("plain text") is None
        assert extract_json("") is None


class TestPromptStackContract:
    """Contract tests for PromptStack API."""

    def test_from_file_exists(self):
        """PromptStack must have a from_file classmethod."""
        from promptfw import PromptStack
        assert hasattr(PromptStack, "from_file")
        assert callable(PromptStack.from_file)

    def test_from_directory_exists(self):
        """PromptStack must have a from_directory classmethod."""
        from promptfw import PromptStack
        assert hasattr(PromptStack, "from_directory")
        assert callable(PromptStack.from_directory)

    def test_from_file_rejects_jinja2_with_helpful_error(self):
        """from_file() on .jinja2 must raise ValueError pointing to frontmatter module."""
        import tempfile
        from promptfw import PromptStack

        with tempfile.NamedTemporaryFile(suffix=".jinja2", delete=False) as f:
            f.write(b"---\nsystem: test\n---\n")
            f.flush()
            with pytest.raises(ValueError, match="frontmatter"):
                PromptStack.from_file(f.name)

    def test_version_at_least_0_7(self):
        """promptfw version must be >= 0.7.0 for SSoT features."""
        from promptfw import __version__
        major, minor = [int(x) for x in __version__.split(".")[:2]]
        assert (major, minor) >= (0, 7), \
            f"promptfw >= 0.7.0 required for SSoT (frontmatter, think-tags), got {__version__}"
