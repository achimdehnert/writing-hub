"""
Contract Tests: aifw/LLMRouter API (ADR-160)

These tests verify that writing-hub's assumptions about LLMRouter's API are correct.
"""


class TestLLMRouterContract:
    """Contract tests for apps.authoring.services.llm_router.LLMRouter."""

    def test_completion_accepts_action_code(self):
        """LLMRouter.completion must accept 'action_code' parameter."""
        from apps.authoring.services.llm_router import LLMRouter
        import inspect

        sig = inspect.signature(LLMRouter.completion)
        params = list(sig.parameters.keys())

        assert "action_code" in params, "LLMRouter.completion must accept 'action_code' parameter"

    def test_completion_accepts_messages(self):
        """LLMRouter.completion must accept 'messages' parameter."""
        from apps.authoring.services.llm_router import LLMRouter
        import inspect

        sig = inspect.signature(LLMRouter.completion)
        params = list(sig.parameters.keys())

        assert "messages" in params, "LLMRouter.completion must accept 'messages' parameter"

    def test_completion_accepts_quality_level_not_quality(self):
        """LLMRouter.completion uses 'quality_level', NOT 'quality'."""
        from apps.authoring.services.llm_router import LLMRouter
        import inspect

        sig = inspect.signature(LLMRouter.completion)
        params = list(sig.parameters.keys())

        assert "quality_level" in params, "LLMRouter.completion should accept 'quality_level' parameter"
        # Note: 'quality' might be in **kwargs, but explicit param is 'quality_level'

    def test_completion_returns_string(self):
        """LLMRouter.completion should return a string."""
        from apps.authoring.services.llm_router import LLMRouter
        import inspect

        sig = inspect.signature(LLMRouter.completion)
        # Check return annotation if available
        if sig.return_annotation != inspect.Signature.empty:
            assert sig.return_annotation is str or "str" in str(sig.return_annotation), (
                f"LLMRouter.completion should return str, got {sig.return_annotation}"
            )


class TestLLMRouterAdapterMapping:
    """Test that _OutlineLLMRouterAdapter correctly maps parameters."""

    def test_adapter_maps_quality_to_quality_level(self):
        """Adapter should map outlinefw 'quality' to LLMRouter 'quality_level'."""
        from apps.authoring.services.outline_service import _OutlineLLMRouterAdapter
        from unittest.mock import MagicMock, patch

        adapter = _OutlineLLMRouterAdapter()

        # Mock the internal router
        with patch.object(adapter, "_router") as mock_router:
            mock_router.completion.return_value = "test response"

            # Create a mock LLMQuality enum
            mock_quality = MagicMock()
            mock_quality.value = 2  # STANDARD

            # Call with outlinefw-style 'quality' parameter
            adapter.completion(
                messages=[{"role": "user", "content": "test"}],
                quality=mock_quality,
            )

            # Verify it was mapped to 'quality_level'
            call_kwargs = mock_router.completion.call_args.kwargs
            assert "quality_level" in call_kwargs, "Adapter should map 'quality' to 'quality_level'"
            assert call_kwargs["quality_level"] == 2
            assert "quality" not in call_kwargs, "Adapter should NOT pass 'quality' to LLMRouter"

    def test_adapter_filters_unknown_kwargs(self):
        """Adapter should not pass unknown kwargs to LLMRouter."""
        from apps.authoring.services.outline_service import _OutlineLLMRouterAdapter
        from unittest.mock import patch

        adapter = _OutlineLLMRouterAdapter()

        with patch.object(adapter, "_router") as mock_router:
            mock_router.completion.return_value = "test response"

            # Call with unknown parameter
            adapter.completion(
                messages=[{"role": "user", "content": "test"}],
                unknown_param="should_be_filtered",
            )

            # Verify unknown param was filtered
            call_kwargs = mock_router.completion.call_args.kwargs
            assert "unknown_param" not in call_kwargs, "Adapter should filter unknown kwargs"
