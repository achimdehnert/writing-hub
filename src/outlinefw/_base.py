"""
outlinefw._base -- Abstract base class for host-app outline service implementations.

Extracted from django_adapter.py so the ABC is importable without Django.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from outlinefw.schemas import LLMQuality, OutlineResult, ProjectContext


class OutlineServiceBase(ABC):
    """Abstract base class for Host-App outline service implementations."""

    @abstractmethod
    def get_tenant_id(self, request: Any) -> int:
        """Extract tenant_id from the current request context."""
        ...

    @abstractmethod
    def persist_outline(
        self,
        result: OutlineResult,
        context: ProjectContext,
        tenant_id: int,
    ) -> Any:
        """Persist the generated outline. Called only if result.success is True."""
        ...

    @abstractmethod
    def get_llm_router(self, tenant_id: int) -> Any:
        """Return a configured LLMRouter for the given tenant."""
        ...

    def generate_and_persist(
        self,
        framework_key: str,
        context: ProjectContext,
        request: Any,
        quality: LLMQuality = LLMQuality.STANDARD,
    ) -> OutlineResult:
        """Template method: generate outline + optionally persist."""
        from outlinefw.generator import OutlineGenerator
        tenant_id = self.get_tenant_id(request)
        router = self.get_llm_router(tenant_id)
        generator = OutlineGenerator(router=router)
        result = generator.generate(framework_key=framework_key, context=context, quality=quality)
        if result.success:
            self.persist_outline(result, context, tenant_id)
        return result


class InMemoryOutlineService(OutlineServiceBase):
    """Concrete implementation for testing -- no Django required."""

    def __init__(self, router: Any, tenant_id: int = 1) -> None:
        self._router = router
        self._tenant_id = tenant_id
        self.persisted: list[dict[str, Any]] = []

    def get_tenant_id(self, request: Any) -> int:
        return self._tenant_id

    def persist_outline(self, result: OutlineResult, context: ProjectContext, tenant_id: int) -> dict[str, Any]:
        record = {
            "framework_key": result.framework_key,
            "title": context.title,
            "tenant_id": tenant_id,
            "nodes": [n.model_dump() for n in result.nodes],
        }
        self.persisted.append(record)
        return record

    def get_llm_router(self, tenant_id: int) -> Any:
        return self._router
