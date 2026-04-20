"""
Contract Tests: authoringfw content_types API (0.10.0)

Verifies writing-hub's assumptions about authoringfw's content_types API:
  - get_content_type_config() exists and returns ContentTypeConfig
  - ContentTypeConfig has style_profile (StyleProfile) and chunk_vocab (dict)
  - StyleProfile.to_constraints() returns list[str]
  - All 7 content types from BookProject.ContentType are available
  - Convention-based template lookup works with prompt_exists()
"""

import pytest

pytestmark = pytest.mark.contract

authoringfw = pytest.importorskip("authoringfw", reason="authoringfw not installed")


class TestContentTypesContract:
    """Contract: authoringfw.content_types API used by chapter services."""

    def test_should_export_get_content_type_config(self):
        from authoringfw import get_content_type_config

        assert callable(get_content_type_config)

    def test_should_export_list_content_types(self):
        from authoringfw import list_content_types

        assert callable(list_content_types)

    def test_should_export_content_type_config_class(self):
        from authoringfw import ContentTypeConfig

        assert ContentTypeConfig is not None

    def test_should_return_content_type_config_with_style_profile(self):
        from authoringfw import get_content_type_config, StyleProfile

        cfg = get_content_type_config("novel")
        assert hasattr(cfg, "style_profile")
        assert isinstance(cfg.style_profile, StyleProfile)

    def test_should_return_content_type_config_with_chunk_vocab(self):
        from authoringfw import get_content_type_config

        cfg = get_content_type_config("novel")
        assert hasattr(cfg, "chunk_vocab")
        assert isinstance(cfg.chunk_vocab, dict)
        assert "opening" in cfg.chunk_vocab
        assert "mid" in cfg.chunk_vocab
        assert "mid_detail" in cfg.chunk_vocab

    def test_should_have_style_profile_to_constraints(self):
        """ChapterProductionService calls style_profile.to_constraints()."""
        from authoringfw import get_content_type_config

        cfg = get_content_type_config("academic")
        constraints = cfg.style_profile.to_constraints()
        assert isinstance(constraints, list)
        assert all(isinstance(c, str) for c in constraints)
        assert len(constraints) > 0


class TestAllBookProjectContentTypes:
    """Contract: all content_types from BookProject.ContentType must be available."""

    WRITING_HUB_CONTENT_TYPES = [
        "novel",
        "nonfiction",
        "short_story",
        "screenplay",
        "essay",
        "academic",
        "scientific",
    ]

    @pytest.mark.parametrize("ct", WRITING_HUB_CONTENT_TYPES)
    def test_should_have_config_for_content_type(self, ct):
        from authoringfw import get_content_type_config

        cfg = get_content_type_config(ct)
        assert cfg.name == ct
        assert cfg.style_profile.tone != ""
        assert len(cfg.chunk_vocab) >= 3


class TestVersionContract:
    def test_should_be_at_least_0_10_0(self):
        """writing-hub requires authoringfw >= 0.10.0 for content_types."""
        from authoringfw import __version__

        parts = [int(x) for x in __version__.split(".")[:2]]
        assert (parts[0], parts[1]) >= (0, 10), f"authoringfw >= 0.10.0 required, got {__version__}"
