"""
Chapter Production Service
===========================

Pipeline: Brief → Write → Analyze → Gate → Commit

Packages:
  - iil-aifw:       sync_completion() via LLMRouter (action_codes: chapter_*)
  - iil-promptfw:   PromptStack fuer strukturierte Prompts
  - iil-authoringfw: StyleProfile fuer Stil-Kontext im Prompt
  - iil-weltenfw:   get_client() fuer Welt/Charakter-Kontext

Kein direkter LLM-Zugriff — ausschliesslich via iil-aifw.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

from apps.core.prompt_utils import render_prompt
from .llm_router import LLMRouter, LLMRoutingError, get_quality_level_for_tier
from .project_context_service import ProjectContextService

logger = logging.getLogger(__name__)


class ProductionStage(str, Enum):
    BRIEF = "brief"
    WRITE = "write"
    ANALYZE = "analyze"
    GATE = "gate"
    REVISE = "revise"
    COMMIT = "commit"


@dataclass
class BriefResult:
    success: bool
    brief: str = ""
    error: str = ""


@dataclass
class WriteResult:
    success: bool
    content: str = ""
    word_count: int = 0
    error: str = ""


@dataclass
class AnalyzeResult:
    success: bool
    overall_score: Decimal = Decimal("0")
    strengths: list[str] = field(default_factory=list)
    issues: list[dict] = field(default_factory=list)
    error: str = ""


@dataclass
class GateResult:
    decision: str = "review"
    allows_commit: bool = False
    reason: str = ""
    required_fixes: list[str] = field(default_factory=list)


@dataclass
class ProductionResult:
    success: bool
    stage: ProductionStage
    chapter_id: str | None = None
    brief: BriefResult | None = None
    write: WriteResult | None = None
    analyze: AnalyzeResult | None = None
    gate: GateResult | None = None
    iterations: int = 1
    duration_seconds: float = 0.0
    error: str = ""


class ChapterProductionService:
    """
    Orchestriert die Kapitel-Produktions-Pipeline.

    Verwendung:
        svc = ChapterProductionService(project_id, user)
        result = svc.produce_chapter(chapter_id)
    """

    def __init__(self, project_id: str, user=None):
        self._project_id = str(project_id)
        self.user = user
        self._router = LLMRouter()
        self._ctx_service = ProjectContextService()
        self._quality_level: int | None = self._resolve_quality_level()
        self._prompt_stack = self._build_prompt_stack()
        self._style_profile = self._load_style_profile()

    def _build_prompt_stack(self):
        """promptfw.PromptStack laden."""
        try:
            from promptfw import PromptStack
            from django.conf import settings
            import os
            templates_dir = getattr(settings, "PROMPT_TEMPLATES_DIR", None)
            if templates_dir and os.path.isdir(templates_dir):
                return PromptStack.from_directory(templates_dir)
            return PromptStack()
        except Exception:
            return None

    def _load_style_profile(self):
        """
        authoringfw.StyleProfile fuer den Projekt-Autor laden.
        Wird in Schreib-Prompts injiziert.
        """
        try:
            from authoringfw import StyleProfile
            from apps.projects.models import BookProject
            project = BookProject.objects.get(pk=self._project_id)
            return StyleProfile(
                tone=getattr(project, "tone", "") or "neutral",
                pov="third_limited",
                tense="past",
            )
        except Exception:
            return None

    def _resolve_quality_level(self) -> int | None:
        try:
            from apps.projects.models import BookProject
            project = BookProject.objects.get(pk=self._project_id)
            tier = getattr(project, "subscription_tier", None)
            if tier:
                return get_quality_level_for_tier(str(tier))
        except Exception:
            pass
        return None

    def _get_style_constraints(self) -> str:
        """authoringfw.StyleProfile.to_constraints() fuer Prompt-Injektion."""
        if self._style_profile is None:
            return ""
        try:
            constraints = self._style_profile.to_constraints()
            if isinstance(constraints, list):
                return "\n".join(f"- {c}" for c in constraints)
            return str(constraints)
        except Exception:
            return ""

    def _get_context_block(self) -> str:
        ctx = self._ctx_service.get_context(self._project_id)
        return ctx.to_prompt_block()

    def generate_brief(self, chapter_id: str) -> BriefResult:
        """Stage 1: Kapitel-Brief via aifw action_code=chapter_brief."""
        from apps.projects.models import OutlineVersion, OutlineNode, BookProject

        try:
            project = BookProject.objects.get(pk=self._project_id)
            version = OutlineVersion.objects.filter(
                project=project, is_active=True
            ).order_by("-created_at").first()
            node = None
            if version:
                node = OutlineNode.objects.filter(
                    outline_version=version, pk=chapter_id
                ).first()

            ctx_block = self._get_context_block()
            style_block = self._get_style_constraints()
            node_text = f"\nKapitel {node.order}: {node.title}\n{node.description}" if node else ""

            messages = render_prompt(
                "authoring/chapter_brief",
                ctx_block=ctx_block,
                style_block=style_block,
                node_text=node_text,
            )
            if not messages:
                messages = [
                    {"role": "system", "content": "Du bist ein Buchschreib-Assistent.\n\n" + ctx_block},
                    {"role": "user", "content": f"Schreib-Brief fuer:{node_text}"},
                ]

            content = self._router.completion(
                "chapter_brief", messages, quality_level=self._quality_level
            )
            return BriefResult(success=True, brief=content)

        except LLMRoutingError as exc:
            return BriefResult(success=False, error=str(exc))
        except Exception as exc:
            logger.exception("generate_brief Fehler")
            return BriefResult(success=False, error=str(exc))

    def write_chapter(
        self, chapter_id: str, brief: str, target_words: int = 2000
    ) -> WriteResult:
        """Stage 2: Kapitel schreiben via aifw action_code=chapter_write."""
        ctx_block = self._get_context_block()
        style_block = self._get_style_constraints()

        messages = render_prompt(
            "authoring/chapter_write_production",
            target_words=target_words,
            ctx_block=ctx_block,
            style_block=style_block,
            brief=brief,
        )
        if not messages:
            messages = [
                {"role": "system", "content": f"Du bist ein Romanautor. Ca. {target_words} Woerter.\n\n" + ctx_block},
                {"role": "user", "content": f"Schreibe das Kapitel:\n\n{brief}"},
            ]

        try:
            content = self._router.completion(
                "chapter_write", messages,
                quality_level=self._quality_level, priority="quality"
            )
            return WriteResult(success=True, content=content, word_count=len(content.split()))
        except LLMRoutingError as exc:
            return WriteResult(success=False, error=str(exc))
        except Exception as exc:
            logger.exception("write_chapter Fehler")
            return WriteResult(success=False, error=str(exc))

    def analyze_chapter(self, chapter_id: str, content: str) -> AnalyzeResult:
        """Stage 3: Qualitaetsanalyse via aifw action_code=chapter_analyze."""
        ctx_block = self._get_context_block()
        style_block = self._get_style_constraints()

        messages = render_prompt(
            "authoring/chapter_analyze",
            ctx_block=ctx_block,
            style_block=style_block,
            content=content,
        )
        if not messages:
            messages = [
                {"role": "system", "content": "Du bist ein Lektor.\n\n" + ctx_block},
                {"role": "user", "content": content[:6000]},
            ]

        try:
            from promptfw.parsing import extract_json
            raw = self._router.completion(
                "chapter_analyze", messages, quality_level=self._quality_level
            )
            data = extract_json(raw)
            if data:
                return AnalyzeResult(
                    success=True,
                    overall_score=Decimal(str(data.get("overall_score", 7.0))),
                    strengths=data.get("strengths", []),
                    issues=data.get("issues", []),
                )
            return AnalyzeResult(success=True, overall_score=Decimal("7.0"))
        except LLMRoutingError as exc:
            return AnalyzeResult(success=False, error=str(exc))
        except Exception as exc:
            logger.exception("analyze_chapter Fehler")
            return AnalyzeResult(success=False, error=str(exc))

    def evaluate_gate(self, analyze: AnalyzeResult) -> GateResult:
        score = float(analyze.overall_score)
        if score >= 8.5:
            return GateResult(decision="approve", allows_commit=True, reason=f"Score {score:.1f} >= 8.5")
        elif score >= 7.0:
            return GateResult(decision="review", allows_commit=False, reason=f"Score {score:.1f} — manuelle Pruefung")
        elif score >= 5.0:
            fixes = [i.get("description", "") for i in analyze.issues[:3]]
            return GateResult(decision="revise", allows_commit=False, required_fixes=fixes, reason=f"Score {score:.1f}")
        return GateResult(decision="reject", allows_commit=False, reason=f"Score {score:.1f} < 5.0")

    def produce_chapter(
        self,
        chapter_id: str,
        target_words: int = 2000,
        max_iterations: int = 3,
        auto_commit: bool = False,
    ) -> ProductionResult:
        """Vollstaendige Pipeline ausfuehren."""
        start = time.time()
        brief_result = self.generate_brief(chapter_id)
        if not brief_result.success:
            return ProductionResult(
                success=False, stage=ProductionStage.BRIEF,
                chapter_id=chapter_id, brief=brief_result,
                error=brief_result.error, duration_seconds=time.time() - start,
            )

        write_result = None
        analyze_result = None
        gate_result = None

        for iteration in range(1, max_iterations + 1):
            write_result = self.write_chapter(chapter_id, brief_result.brief, target_words)
            if not write_result.success:
                return ProductionResult(
                    success=False, stage=ProductionStage.WRITE,
                    chapter_id=chapter_id, brief=brief_result, write=write_result,
                    iterations=iteration, error=write_result.error,
                    duration_seconds=time.time() - start,
                )
            analyze_result = self.analyze_chapter(chapter_id, write_result.content)
            gate_result = self.evaluate_gate(analyze_result)

            if gate_result.allows_commit or not gate_result.required_fixes:
                break

            if iteration < max_iterations:
                fixes = "\n".join(f"- {f}" for f in gate_result.required_fixes)
                brief_result = BriefResult(
                    success=True,
                    brief=brief_result.brief + f"\n\n## Revision {iteration}\n" + fixes,
                )

        return ProductionResult(
            success=True,
            stage=ProductionStage.COMMIT if (auto_commit and gate_result and gate_result.allows_commit) else ProductionStage.GATE,
            chapter_id=chapter_id,
            brief=brief_result,
            write=write_result,
            analyze=analyze_result,
            gate=gate_result,
            iterations=iteration,
            duration_seconds=time.time() - start,
        )


def get_chapter_production_service(project_id: str, user=None) -> ChapterProductionService:
    return ChapterProductionService(project_id=project_id, user=user)
