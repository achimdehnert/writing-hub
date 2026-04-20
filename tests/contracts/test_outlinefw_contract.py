"""
Contract Tests: outlinefw API (ADR-160)

These tests verify that writing-hub's assumptions about outlinefw's API are correct.
They would have caught all the recent API mismatch errors before deployment.
"""

import pytest


class TestOutlineGeneratorContract:
    """Contract tests for outlinefw.OutlineGenerator."""

    @pytest.fixture
    def outlinefw_available(self):
        """Skip if outlinefw not installed."""
        try:
            from outlinefw import OutlineGenerator  # noqa: F401

            return True
        except ImportError:
            pytest.skip("outlinefw not installed")

    def test_init_accepts_router_parameter(self, outlinefw_available):
        """OutlineGenerator.__init__ must accept 'router' parameter."""
        from outlinefw import OutlineGenerator
        import inspect

        sig = inspect.signature(OutlineGenerator.__init__)
        params = list(sig.parameters.keys())

        assert "router" in params, "OutlineGenerator.__init__ must accept 'router' parameter"
        assert "llm_router" not in params, "Wrong parameter name: use 'router', not 'llm_router'"

    def test_generate_accepts_framework_key_parameter(self, outlinefw_available):
        """OutlineGenerator.generate must accept 'framework_key' parameter."""
        from outlinefw import OutlineGenerator
        import inspect

        sig = inspect.signature(OutlineGenerator.generate)
        params = list(sig.parameters.keys())

        assert "framework_key" in params, "OutlineGenerator.generate must accept 'framework_key' parameter"
        assert "framework" not in params, "Wrong parameter name: use 'framework_key', not 'framework'"

    def test_generate_accepts_context_parameter(self, outlinefw_available):
        """OutlineGenerator.generate must accept 'context' parameter."""
        from outlinefw import OutlineGenerator
        import inspect

        sig = inspect.signature(OutlineGenerator.generate)
        params = list(sig.parameters.keys())

        assert "context" in params, "OutlineGenerator.generate must accept 'context' parameter"

    def test_generate_does_not_accept_chapter_count(self, outlinefw_available):
        """OutlineGenerator.generate must NOT accept 'chapter_count' parameter."""
        from outlinefw import OutlineGenerator
        import inspect

        sig = inspect.signature(OutlineGenerator.generate)
        params = list(sig.parameters.keys())

        assert "chapter_count" not in params, "OutlineGenerator.generate does not have 'chapter_count' parameter"

    def test_generate_accepts_quality_parameter(self, outlinefw_available):
        """OutlineGenerator.generate should accept 'quality' parameter."""
        from outlinefw import OutlineGenerator
        import inspect

        sig = inspect.signature(OutlineGenerator.generate)
        params = list(sig.parameters.keys())

        assert "quality" in params, "OutlineGenerator.generate should accept 'quality' parameter"


class TestFrameworksContract:
    """Contract tests for outlinefw.frameworks."""

    @pytest.fixture
    def outlinefw_available(self):
        try:
            from outlinefw.frameworks import FRAMEWORKS  # noqa: F401

            return True
        except ImportError:
            pytest.skip("outlinefw not installed")

    def test_known_frameworks_exist(self, outlinefw_available):
        """Verify expected frameworks are available."""
        from outlinefw.frameworks import FRAMEWORKS

        expected = ["three_act", "save_the_cat", "heros_journey", "five_act", "dan_harmon"]
        for key in expected:
            assert key in FRAMEWORKS, f"Expected framework '{key}' not found"

    def test_nonfiction_frameworks_in_outlinefw(self, outlinefw_available):
        """Verify nonfiction frameworks are natively available in outlinefw v0.3.1+."""
        from outlinefw.frameworks import FRAMEWORKS

        # Since v0.3.1 outlinefw ships nonfiction frameworks natively (no mapping needed)
        nonfiction_frameworks = ["scientific_essay", "academic_essay", "essay"]
        for key in nonfiction_frameworks:
            assert key in FRAMEWORKS, f"Expected nonfiction framework '{key}' in outlinefw v0.3.1+"


class TestProjectContextContract:
    """Contract tests for outlinefw.ProjectContext."""

    @pytest.fixture
    def outlinefw_available(self):
        try:
            from outlinefw import ProjectContext  # noqa: F401

            return True
        except ImportError:
            pytest.skip("outlinefw not installed")

    def test_project_context_required_fields(self, outlinefw_available):
        """Verify ProjectContext has expected required fields."""
        from outlinefw import ProjectContext

        # Use model_fields (Pydantic v2) — more reliable than inspect.signature
        expected_fields = ["title", "genre", "logline"]
        for field in expected_fields:
            assert field in ProjectContext.model_fields, f"ProjectContext should have '{field}' field"


class TestLLMQualityContract:
    """Contract tests for outlinefw.LLMQuality enum."""

    @pytest.fixture
    def outlinefw_available(self):
        try:
            from outlinefw import LLMQuality  # noqa: F401

            return True
        except ImportError:
            pytest.skip("outlinefw not installed")

    def test_llm_quality_has_value_attribute(self, outlinefw_available):
        """LLMQuality enum members should have .value attribute."""
        from outlinefw import LLMQuality

        # Verify we can access .value for mapping to LLMRouter.quality_level
        assert hasattr(LLMQuality.STANDARD, "value"), "LLMQuality.STANDARD should have .value attribute"

    def test_llm_quality_values_are_integers(self, outlinefw_available):
        """LLMQuality enum values should be integers for LLMRouter mapping."""
        from outlinefw import LLMQuality

        for member in LLMQuality:
            assert isinstance(member.value, int), (
                f"LLMQuality.{member.name}.value should be int, got {type(member.value)}"
            )
