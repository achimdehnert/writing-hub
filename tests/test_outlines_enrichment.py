"""
Tests for apps.outlines.services — enrich_node() via fieldprefill (ADR-107).

Tests the fieldprefill integration: prefill_fields() call, result mapping,
error handling. Also covers the retriever registration.
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from fieldprefill.result import PrefillResult
from fieldprefill.retrievers import clear_registry, list_retrievers, get_context_texts


class TestEnrichNodeWithFieldprefill:
    """Test enrich_node() delegates to prefill_fields() correctly."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        """Create a mock OutlineNode with required attributes."""
        self.node = MagicMock()
        self.node.pk = 42
        self.node.order = 3
        self.node.title = "Der dunkle Wald"
        self.node.beat_phase = "Midpoint"
        self.node.act = "Act II"
        self.node.target_words = 5000
        self.node.description = "Ein erster Entwurf."
        self.node.emotional_arc = ""
        self.node.outline_version.project.owner_id = 1
        self.node.outline_version.project.pk = "proj-123"
        self.node.outline_version.project.title = "Testprojekt"
        self.node.outline_version.project.genre = "Thriller"

    @patch("fieldprefill.prefill_fields")
    def test_enrich_node_calls_prefill_fields(self, mock_prefill):
        """enrich_node() must call prefill_fields with correct parameters."""
        from apps.outlines.services import OutlineGenerationService

        mock_prefill.return_value = PrefillResult(
            content='{"description": "Detailliert", "emotional_arc": "spannend"}',
            tokens_used=200,
            model="gpt-4o",
            latency_ms=800,
            field_key="description,emotional_arc",
        )

        svc = OutlineGenerationService()
        result = svc.enrich_node(self.node)

        assert result["success"] is True
        mock_prefill.assert_called_once()
        call_kwargs = mock_prefill.call_args.kwargs
        assert call_kwargs["field_keys"] == ["description", "emotional_arc"]
        assert call_kwargs["action_code"] == "chapter_outline"
        assert call_kwargs["scope"] == "writing.outline_enrichment"
        assert "project_context" in call_kwargs["sources"]
        assert "outline_siblings" in call_kwargs["sources"]

    @patch("fieldprefill.prefill_fields")
    def test_enrich_node_maps_json_to_fields(self, mock_prefill):
        """JSON response fields are mapped back to node attributes."""
        from apps.outlines.services import OutlineGenerationService

        mock_prefill.return_value = PrefillResult(
            content='{"description": "Neue Beschreibung", "emotional_arc": "aufsteigend"}',
            field_key="description,emotional_arc",
        )

        svc = OutlineGenerationService()
        svc.enrich_node(self.node)

        # Verify node fields were updated
        assert self.node.description == "Neue Beschreibung"
        assert self.node.emotional_arc == "aufsteigend"
        self.node.save.assert_called_once_with(
            update_fields=["description", "emotional_arc"]
        )

    @patch("fieldprefill.prefill_fields")
    def test_enrich_node_plain_text_fallback(self, mock_prefill):
        """If LLM returns plain text (no JSON), use as description."""
        from apps.outlines.services import OutlineGenerationService

        mock_prefill.return_value = PrefillResult(
            content="Just a plain text description without JSON.",
            field_key="description,emotional_arc",
        )

        svc = OutlineGenerationService()
        result = svc.enrich_node(self.node)

        assert result["success"] is True
        assert self.node.description == "Just a plain text description without JSON."
        self.node.save.assert_called_once()

    @patch("fieldprefill.prefill_fields")
    def test_enrich_node_error_from_prefill(self, mock_prefill):
        """If prefill returns an error, enrich_node reports failure."""
        from apps.outlines.services import OutlineGenerationService

        mock_prefill.return_value = PrefillResult(
            content="",
            error="API key invalid",
            field_key="description,emotional_arc",
        )

        svc = OutlineGenerationService()
        result = svc.enrich_node(self.node)

        assert result["success"] is False
        assert "KI nicht verfügbar" in result["error"]
        self.node.save.assert_not_called()

    @patch("fieldprefill.prefill_fields")
    def test_enrich_node_exception_handling(self, mock_prefill):
        """Exceptions are caught and returned as error dict."""
        from apps.outlines.services import OutlineGenerationService

        mock_prefill.side_effect = RuntimeError("Connection timeout")

        svc = OutlineGenerationService()
        result = svc.enrich_node(self.node)

        assert result["success"] is False
        assert "Connection timeout" in result["error"]

    @patch("fieldprefill.prefill_fields")
    def test_enrich_node_passes_context_from_node(self, mock_prefill):
        """Context dict includes node metadata for cross-field reference."""
        from apps.outlines.services import OutlineGenerationService

        mock_prefill.return_value = PrefillResult(content="{}", field_key="x")

        svc = OutlineGenerationService()
        svc.enrich_node(self.node)

        call_kwargs = mock_prefill.call_args.kwargs
        ctx = call_kwargs["context"]
        assert ctx["beat_phase"] == "Midpoint"
        assert ctx["act"] == "Act II"
        assert ctx["title"] == "Der dunkle Wald"
        assert ctx["order"] == "3"

    @patch("fieldprefill.prefill_fields")
    def test_enrich_node_empty_description_uses_placeholder(self, mock_prefill):
        """Empty node description is replaced with placeholder in prompt."""
        from apps.outlines.services import OutlineGenerationService

        self.node.description = "  "
        mock_prefill.return_value = PrefillResult(content="{}", field_key="x")

        svc = OutlineGenerationService()
        svc.enrich_node(self.node)

        prompt = mock_prefill.call_args.kwargs["prompt"]
        assert "(noch kein Inhalt)" in prompt


class TestRetrieverRegistration:
    """Test that retrievers register correctly and return expected data."""

    def test_should_have_project_context_retriever(self):
        """project_context retriever must be registered after AppConfig.ready()."""
        # Django AppConfig.ready() already called register_all() during setup
        # The retrievers are registered via @register_retriever decorator at import time
        from apps.outlines.retrievers import _get_project_context
        assert callable(_get_project_context)

    def test_should_have_outline_siblings_retriever(self):
        """outline_siblings retriever must be registered."""
        from apps.outlines.retrievers import _get_outline_siblings
        assert callable(_get_outline_siblings)

    def test_project_context_returns_fallback_without_instance(self):
        """project_context retriever returns empty list without instance."""
        from apps.outlines.retrievers import _get_project_context
        result = _get_project_context(owner_id=1, instance=None)
        assert result == []

    def test_outline_siblings_returns_empty_without_instance(self):
        """outline_siblings retriever returns empty list without instance."""
        from apps.outlines.retrievers import _get_outline_siblings
        result = _get_outline_siblings(owner_id=1, instance=None)
        assert result == []

    def test_project_context_fallback_on_service_error(self):
        """project_context uses title+genre fallback if service fails."""
        from apps.outlines.retrievers import _get_project_context

        mock_project = MagicMock()
        mock_project.title = "Mein Roman"
        mock_project.genre = "Fantasy"
        mock_project.pk = "p-1"

        with patch(
            "apps.authoring.services.project_context_service.ProjectContextService",
            side_effect=ImportError("not available"),
        ):
            result = _get_project_context(owner_id=1, instance=mock_project)

        assert len(result) == 1
        assert "Mein Roman" in result[0]
        assert "Fantasy" in result[0]


class TestFieldprefillContract:
    """Contract tests: verify fieldprefill API matches our expectations."""

    def test_should_have_prefill_fields_function(self):
        """fieldprefill must export prefill_fields."""
        from fieldprefill import prefill_fields
        assert callable(prefill_fields)

    def test_should_have_as_dict_on_result(self):
        """PrefillResult must have as_dict() method."""
        r = PrefillResult(content='{"a": 1}')
        assert hasattr(r, "as_dict")
        assert r.as_dict() == {"a": 1}

    def test_should_have_get_on_result(self):
        """PrefillResult must have get() method."""
        r = PrefillResult(content='{"key": "val"}')
        assert r.get("key") == "val"
        assert r.get("missing", "default") == "default"

    def test_version_at_least_0_2_0(self):
        """fieldprefill must be >= 0.2.0 for multi-field support."""
        import fieldprefill
        parts = fieldprefill.__version__.split(".")
        major, minor = int(parts[0]), int(parts[1])
        assert (major, minor) >= (0, 2), \
            f"Need fieldprefill >= 0.2.0, got {fieldprefill.__version__}"
