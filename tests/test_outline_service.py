"""
Tests for apps.authoring.services.outline_service — OutlineGeneratorService.

These tests verify the contract between writing-hub and iil-outlinefw.
They would have caught the 'framework' vs 'framework_key' parameter mismatch.
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock


class TestOutlineGeneratorServiceContract:
    """Contract tests: verify we call outlinefw API correctly."""

    @pytest.fixture
    def mock_project_context(self):
        """Mock ProjectContext from outlinefw."""
        ctx = MagicMock()
        ctx.title = "Test Project"
        ctx.genre = "Thriller"
        ctx.logline = "A test logline"
        ctx.protagonist = "Test Hero"
        ctx.setting = "Test Setting"
        return ctx

    @patch("apps.authoring.services.outline_service._project_context_from_db")
    @patch("apps.authoring.services.outline_service.OutlineGenerator")
    def test_generate_calls_outlinefw_with_correct_parameters(
        self, MockGenerator, mock_ctx_from_db, mock_project_context
    ):
        """OutlineGeneratorService.generate() must use correct parameter names."""
        from apps.authoring.services.outline_service import OutlineGeneratorService

        # Setup
        mock_ctx_from_db.return_value = mock_project_context
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.nodes = []
        mock_instance.generate.return_value = mock_result
        MockGenerator.return_value = mock_instance

        # Execute
        service = OutlineGeneratorService()
        service.generate_outline(
            project_id="test-project-id",
            framework="save_the_cat",
            chapter_count=12,
        )

        # Verify: generate() was called with correct parameter names
        mock_instance.generate.assert_called_once()
        call_kwargs = mock_instance.generate.call_args.kwargs

        # Contract assertions - these are the critical checks
        assert "framework_key" in call_kwargs, \
            "Must use 'framework_key', not 'framework' (outlinefw API)"
        assert "context" in call_kwargs, \
            "Must pass 'context' parameter"
        assert "chapter_count" not in call_kwargs, \
            "outlinefw.generate() does not accept 'chapter_count'"
        assert "framework" not in call_kwargs, \
            "Wrong parameter name: use 'framework_key' instead of 'framework'"

    @patch("apps.authoring.services.outline_service._project_context_from_db")
    @patch("apps.authoring.services.outline_service.OutlineGenerator")
    def test_generate_passes_quality_parameter(
        self, MockGenerator, mock_ctx_from_db, mock_project_context
    ):
        """Quality parameter should be passed through correctly."""
        from apps.authoring.services.outline_service import OutlineGeneratorService

        mock_ctx_from_db.return_value = mock_project_context
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        MockGenerator.return_value = mock_instance
        mock_instance.generate.return_value = mock_result

        service = OutlineGeneratorService()
        service.generate_outline(
            project_id="test-id",
            framework="heros_journey",
            chapter_count=15,
            quality="high",
        )

        call_kwargs = mock_instance.generate.call_args.kwargs
        assert "quality" in call_kwargs

    @patch("apps.authoring.services.outline_service._project_context_from_db")
    def test_generate_returns_fallback_when_context_missing(self, mock_ctx_from_db):
        """Should return error result when project context cannot be built."""
        from apps.authoring.services.outline_service import OutlineGeneratorService

        mock_ctx_from_db.return_value = None

        service = OutlineGeneratorService()
        result = service.generate_outline(
            project_id="nonexistent",
            framework="save_the_cat",
            chapter_count=12,
        )

        assert result.success is False
        assert "Projektkontext" in result.error_message


class TestOutlineGeneratorServiceIntegration:
    """Integration tests with real outlinefw (if available)."""

    def test_outlinefw_api_signature_matches_expectations(self):
        """Verify outlinefw.OutlineGenerator.generate() has expected signature."""
        try:
            from outlinefw import OutlineGenerator
            import inspect

            sig = inspect.signature(OutlineGenerator.generate)
            params = list(sig.parameters.keys())

            # These are the parameters we expect
            assert "framework_key" in params, \
                "outlinefw API changed: 'framework_key' parameter missing"
            assert "context" in params, \
                "outlinefw API changed: 'context' parameter missing"

            # These should NOT be parameters
            assert "framework" not in params, \
                "outlinefw API uses 'framework_key', not 'framework'"
            assert "chapter_count" not in params, \
                "outlinefw API does not have 'chapter_count' parameter"

        except ImportError:
            pytest.skip("outlinefw not installed")
