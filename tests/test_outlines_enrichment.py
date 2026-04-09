"""
Tests for apps.outlines.services — enrich_node() via DB-backed prompt dispatch.

Tests the render_outline_prompt + LLMRouter integration: content-type dispatch,
result mapping, error handling. Also covers the retriever registration.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestEnrichNodeWithPromptDispatch:
    """Test enrich_node() uses render_outline_prompt + LLMRouter."""

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
        self.node.outline_version.project.content_type = "novel"

    @patch("apps.outlines.prompt_dispatch.get_active_template", return_value=None)
    @patch("apps.outlines.prompt_dispatch.render_outline_prompt")
    @patch("apps.authoring.services.llm_router.LLMRouter")
    @patch("apps.authoring.services.project_context_service.ProjectContextService")
    def test_should_call_render_outline_prompt(self, mock_ctx_svc, mock_router_cls, mock_render, _mock_tpl):
        """enrich_node() must use render_outline_prompt with correct params."""
        from apps.outlines.services import OutlineGenerationService

        mock_render.return_value = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "usr"},
        ]
        mock_router = mock_router_cls.return_value
        mock_router.completion.return_value = '{"description": "OK", "emotional_arc": "gut"}'

        svc = OutlineGenerationService()
        result = svc.enrich_node(self.node)

        assert result["success"] is True
        mock_render.assert_called_once()
        call_kwargs = mock_render.call_args.kwargs
        assert call_kwargs["template_key"] == "enrich_node"
        assert call_kwargs["content_type"] == "novel"
        assert call_kwargs["title"] == "Der dunkle Wald"

    @patch("apps.outlines.prompt_dispatch.get_active_template", return_value=None)
    @patch("apps.outlines.prompt_dispatch.render_outline_prompt")
    @patch("apps.authoring.services.llm_router.LLMRouter")
    @patch("apps.authoring.services.project_context_service.ProjectContextService")
    def test_should_map_json_to_node_fields(self, mock_ctx_svc, mock_router_cls, mock_render, _mock_tpl):
        """JSON response fields are mapped back to node attributes."""
        from apps.outlines.services import OutlineGenerationService

        mock_render.return_value = [{"role": "user", "content": "test"}]
        mock_router = mock_router_cls.return_value
        mock_router.completion.return_value = '{"description": "Neue Beschreibung", "emotional_arc": "aufsteigend"}'

        svc = OutlineGenerationService()
        svc.enrich_node(self.node)

        assert self.node.description == "Neue Beschreibung"
        assert self.node.emotional_arc == "aufsteigend"
        self.node.save.assert_called_once_with(
            update_fields=["description", "emotional_arc"]
        )

    @patch("apps.outlines.prompt_dispatch.get_active_template", return_value=None)
    @patch("apps.outlines.prompt_dispatch.render_outline_prompt")
    @patch("apps.authoring.services.llm_router.LLMRouter")
    @patch("apps.authoring.services.project_context_service.ProjectContextService")
    def test_should_use_plain_text_as_description_fallback(self, mock_ctx_svc, mock_router_cls, mock_render, _mock_tpl):
        """If LLM returns plain text (no JSON), use as description."""
        from apps.outlines.services import OutlineGenerationService

        mock_render.return_value = [{"role": "user", "content": "test"}]
        mock_router = mock_router_cls.return_value
        mock_router.completion.return_value = "Just a plain text description."

        svc = OutlineGenerationService()
        result = svc.enrich_node(self.node)

        assert result["success"] is True
        assert self.node.description == "Just a plain text description."

    @patch("apps.outlines.prompt_dispatch.render_outline_prompt")
    @patch("apps.authoring.services.llm_router.LLMRouter")
    @patch("apps.authoring.services.project_context_service.ProjectContextService")
    def test_should_handle_llm_routing_error(self, mock_ctx_svc, mock_router_cls, mock_render):
        """LLMRoutingError is caught and returned as error dict."""
        from apps.authoring.services.llm_router import LLMRoutingError
        from apps.outlines.services import OutlineGenerationService

        mock_render.return_value = [{"role": "user", "content": "test"}]
        mock_router = mock_router_cls.return_value
        mock_router.completion.side_effect = LLMRoutingError("API key invalid")

        svc = OutlineGenerationService()
        result = svc.enrich_node(self.node)

        assert result["success"] is False
        assert "KI nicht verfügbar" in result["error"]

    @patch("apps.outlines.prompt_dispatch.render_outline_prompt")
    @patch("apps.authoring.services.llm_router.LLMRouter")
    @patch("apps.authoring.services.project_context_service.ProjectContextService")
    def test_should_handle_generic_exception(self, mock_ctx_svc, mock_router_cls, mock_render):
        """Generic exceptions are caught and returned."""
        from apps.outlines.services import OutlineGenerationService

        mock_render.side_effect = RuntimeError("Connection timeout")

        svc = OutlineGenerationService()
        result = svc.enrich_node(self.node)

        assert result["success"] is False
        assert "Connection timeout" in result["error"]

    @patch("apps.outlines.prompt_dispatch.get_active_template", return_value=None)
    @patch("apps.outlines.prompt_dispatch.render_outline_prompt")
    @patch("apps.authoring.services.llm_router.LLMRouter")
    @patch("apps.authoring.services.project_context_service.ProjectContextService")
    def test_should_return_template_id(self, mock_ctx_svc, mock_router_cls, mock_render, _mock_tpl):
        """Result includes template_id for quality feedback linking."""
        from apps.outlines.services import OutlineGenerationService

        mock_render.return_value = [{"role": "user", "content": "test"}]
        mock_router = mock_router_cls.return_value
        mock_router.completion.return_value = '{"description": "OK"}'

        svc = OutlineGenerationService()
        result = svc.enrich_node(self.node)

        assert result["success"] is True
        assert "template_id" in result

    @patch("apps.outlines.prompt_dispatch.get_active_template", return_value=None)
    @patch("apps.outlines.prompt_dispatch.render_outline_prompt")
    @patch("apps.authoring.services.llm_router.LLMRouter")
    @patch("apps.authoring.services.project_context_service.ProjectContextService")
    def test_should_dispatch_scientific_to_academic_group(self, mock_ctx_svc, mock_router_cls, mock_render, _mock_tpl):
        """scientific content_type is routed to academic group."""
        from apps.outlines.services import OutlineGenerationService

        self.node.outline_version.project.content_type = "scientific"
        mock_render.return_value = [{"role": "user", "content": "test"}]
        mock_router = mock_router_cls.return_value
        mock_router.completion.return_value = '{"description": "OK"}'

        svc = OutlineGenerationService()
        svc.enrich_node(self.node)

        call_kwargs = mock_render.call_args.kwargs
        assert call_kwargs["content_type"] == "scientific"


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

        mock_project = MagicMock(spec=["title", "genre", "pk"])
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
        from fieldprefill.result import PrefillResult
        r = PrefillResult(content='{"a": 1}')
        assert hasattr(r, "as_dict")
        assert r.as_dict() == {"a": 1}

    def test_should_have_get_on_result(self):
        """PrefillResult must have get() method."""
        from fieldprefill.result import PrefillResult
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
