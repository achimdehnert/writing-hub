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
import re
import time
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

from apps.authoring.defaults import (
    CHUNK_CONTEXT_WINDOW,
    DEFAULT_CONTENT_TYPE,
    DEFAULT_TARGET_WORD_COUNT,
    MAX_QUALITY_ISSUES,
    MAX_TOKENS_WRITE,
)
from apps.core.prompt_utils import render_prompt
from .llm_router import LLMRouter, LLMRoutingError, get_quality_level_for_tier
from .project_context_service import ProjectContextService

logger = logging.getLogger(__name__)

_DEFAULT_TEMPLATE = "authoring/chapter_write_default"

# Regex: strip leading markdown headings like "# Kapitel 1: Title" or "### Title"
_CHAPTER_HEADING_RE = re.compile(
    r"\A\s*#{1,4}\s*(Kapitel\s*\d+[:.\s]*)?[^\n]*\n+",
    re.IGNORECASE,
)


def _strip_chapter_heading(content: str) -> str:
    """Remove redundant chapter title heading from LLM output.

    The chapter title is stored separately in OutlineNode.title,
    so it must not appear inside the content body.
    """
    return _CHAPTER_HEADING_RE.sub("", content).strip()


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

    def __init__(self, project_id: str, user=None, llm_overrides: dict | None = None):
        self._project_id = str(project_id)
        self.user = user
        self._router = LLMRouter()
        self._ctx_service = ProjectContextService()
        self._content_type = self._resolve_content_type()
        self._ct_config = self._load_content_type_config()
        self._quality_level: int | None = self._resolve_quality_level()
        self._prompt_stack = self._build_prompt_stack()
        self._style_profile = self._ct_config.style_profile
        self._llm_overrides: dict = llm_overrides or {}

    def _resolve_content_type(self) -> str:
        try:
            from apps.projects.models import BookProject

            project = BookProject.objects.get(pk=self._project_id)
            return project.content_type or DEFAULT_CONTENT_TYPE
        except Exception as exc:
            logger.debug("Content type resolution failed: %s", exc)
            return DEFAULT_CONTENT_TYPE

    def _load_content_type_config(self):
        """Load style + chunk_vocab from authoringfw bundled YAML."""
        from authoringfw import get_content_type_config

        return get_content_type_config(self._content_type)

    def _write_template(self) -> str:
        """Resolve write template: content_type → group → default.

        Lookup chain:
          1. chapter_write_{content_type}  (e.g. chapter_write_scientific)
          2. chapter_write_{group}         (e.g. chapter_write_academic)
          3. chapter_write_default
        """
        from apps.core.prompt_utils import prompt_exists
        from apps.projects.constants import CONTENT_TYPE_GROUPS

        ct_template = f"authoring/chapter_write_{self._content_type}"
        if prompt_exists(ct_template):
            return ct_template
        group = CONTENT_TYPE_GROUPS.get(self._content_type, "")
        if group:
            group_template = f"authoring/chapter_write_{group}"
            if prompt_exists(group_template):
                logger.info(
                    "Template fallback: %s → %s (group: %s)",
                    self._content_type,
                    group_template,
                    group,
                )
                return group_template
        return _DEFAULT_TEMPLATE

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
        except Exception as exc:
            logger.debug("PromptStack loading failed: %s", exc)
            return None

    def _resolve_quality_level(self) -> int | None:
        try:
            from apps.projects.models import BookProject

            project = BookProject.objects.get(pk=self._project_id)
            tier = getattr(project, "subscription_tier", None)
            if tier:
                return get_quality_level_for_tier(str(tier))
        except Exception as exc:
            logger.debug("Quality level resolution failed: %s", exc)
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
        except Exception as exc:
            logger.debug("Style constraints failed: %s", exc)
            return ""

    def _get_context_block(self) -> str:
        ctx = self._ctx_service.get_context(self._project_id)
        return ctx.to_prompt_block()

    def generate_brief(self, chapter_id: str) -> BriefResult:
        """Stage 1: Kapitel-Brief via aifw action_code=chapter_brief."""
        from apps.projects.models import OutlineVersion, OutlineNode, BookProject

        try:
            project = BookProject.objects.get(pk=self._project_id)
            version = OutlineVersion.objects.filter(project=project, is_active=True).order_by("-created_at").first()
            node = None
            if version:
                node = OutlineNode.objects.filter(outline_version=version, pk=chapter_id).first()

            ctx_block = self._get_context_block()
            style_block = self._get_style_constraints()
            node_text = ""
            if node:
                node_text = f"\nKapitel {node.order}: {node.title}\n{node.description}"
                if node.notes:
                    node_text += f"\n\nRecherche-Notizen:\n{node.notes}"

            messages = render_prompt(
                "authoring/chapter_brief",
                ctx_block=ctx_block,
                style_block=style_block,
                node_text=node_text,
            )

            content = self._router.completion(
                "chapter_brief",
                messages,
                quality_level=self._quality_level,
                **{k: v for k, v in self._llm_overrides.items() if k == "model"},
            )
            return BriefResult(success=True, brief=content)

        except LLMRoutingError as exc:
            return BriefResult(success=False, error=str(exc))
        except Exception as exc:
            logger.exception("generate_brief Fehler")
            return BriefResult(success=False, error=str(exc))

    def write_chapter(self, chapter_id: str, brief: str, target_words: int = DEFAULT_TARGET_WORD_COUNT) -> WriteResult:
        """Stage 2: Kapitel schreiben via aifw action_code=chapter_write.

        Uses chunked generation (authoringfw pattern) for chapters
        exceeding single-call token capacity (~2500 words).
        """
        from authoringfw.writing.chunked import compute_max_tokens, compute_words_per_chunk

        ctx_block = self._get_context_block()
        style_block = self._get_style_constraints()
        dynamic_max_tokens = compute_max_tokens(target_words)
        words_per_chunk = compute_words_per_chunk(min(dynamic_max_tokens, MAX_TOKENS_WRITE))

        try:
            if target_words <= words_per_chunk:
                return self._write_single(
                    brief,
                    target_words,
                    ctx_block,
                    style_block,
                    dynamic_max_tokens,
                )
            return self._write_chunked(
                brief,
                target_words,
                ctx_block,
                style_block,
                dynamic_max_tokens,
                words_per_chunk,
            )
        except LLMRoutingError as exc:
            return WriteResult(success=False, error=str(exc))
        except Exception as exc:
            logger.exception("write_chapter Fehler")
            return WriteResult(success=False, error=str(exc))

    def _write_single(
        self,
        brief: str,
        target_words: int,
        ctx_block: str,
        style_block: str,
        max_tokens: int,
    ) -> WriteResult:
        """Single-shot chapter generation."""
        messages = render_prompt(
            self._write_template(),
            target_words=target_words,
            ctx_block=ctx_block,
            style_block=style_block,
            brief=brief,
        )
        write_overrides = {"max_tokens": max_tokens}
        write_overrides.update(self._llm_overrides)
        content = self._router.completion(
            "chapter_write",
            messages,
            quality_level=self._quality_level,
            priority="quality",
            **write_overrides,
        )
        content = _strip_chapter_heading(content)
        return WriteResult(success=True, content=content, word_count=len(content.split()))

    def _write_chunked(
        self,
        brief: str,
        target_words: int,
        ctx_block: str,
        style_block: str,
        max_tokens: int,
        words_per_chunk: int,
    ) -> WriteResult:
        """Multi-chunk chapter generation for long chapters."""
        num_chunks = (target_words // words_per_chunk) + 1
        logger.info(
            "Chunked generation: %d words in %d chunks of ~%d words",
            target_words,
            num_chunks,
            words_per_chunk,
        )

        vocab = self._ct_config.chunk_vocab
        tpl = self._write_template()
        all_parts: list[str] = []
        for chunk_num in range(num_chunks):
            is_first = chunk_num == 0
            is_last = chunk_num == num_chunks - 1

            if is_first:
                chunk_brief = (
                    f"{brief}\n\nSchreibe etwa {words_per_chunk} Wörter "
                    f"(Teil 1/{num_chunks}). Beginne mit einer "
                    f"{vocab['opening']}. ENDE NICHT — das Kapitel wird fortgesetzt."
                )
            elif is_last:
                prev_excerpt = "\n\n".join(all_parts[-2:])[-CHUNK_CONTEXT_WINDOW:]
                chunk_brief = (
                    f"BISHERIGER INHALT (Auszug):\n{prev_excerpt}\n\n"
                    f"Schreibe das ENDE des Kapitels (~{words_per_chunk} Wörter, "
                    f"Teil {chunk_num + 1}/{num_chunks}). "
                    "Schließe das Kapitel ab."
                )
            else:
                prev_excerpt = "\n\n".join(all_parts[-2:])[-CHUNK_CONTEXT_WINDOW:]
                chunk_brief = (
                    f"BISHERIGER INHALT (Auszug):\n{prev_excerpt}\n\n"
                    f"{vocab['mid']} (~{words_per_chunk} Wörter, "
                    f"Teil {chunk_num + 1}/{num_chunks}). "
                    f"{vocab['mid_detail']}. ENDE NICHT."
                )

            messages = render_prompt(
                tpl,
                target_words=words_per_chunk,
                ctx_block=ctx_block,
                style_block=style_block,
                brief=chunk_brief,
            )
            write_overrides = {"max_tokens": max_tokens}
            write_overrides.update(self._llm_overrides)

            try:
                chunk_content = self._router.completion(
                    "chapter_write",
                    messages,
                    quality_level=self._quality_level,
                    priority="quality",
                    **write_overrides,
                )
                all_parts.append(chunk_content.strip())
                logger.info(
                    "Chunk %d/%d: %d words",
                    chunk_num + 1,
                    num_chunks,
                    len(chunk_content.split()),
                )
            except (LLMRoutingError, Exception) as exc:
                if all_parts:
                    logger.warning(
                        "Chunk %d/%d failed, returning partial: %s",
                        chunk_num + 1,
                        num_chunks,
                        exc,
                    )
                    partial = "\n\n".join(all_parts)
                    return WriteResult(
                        success=True,
                        content=partial,
                        word_count=len(partial.split()),
                    )
                raise

        full_content = "\n\n".join(all_parts)
        full_content = _strip_chapter_heading(full_content)
        return WriteResult(
            success=True,
            content=full_content,
            word_count=len(full_content.split()),
        )

    def analyze_chapter(self, chapter_id: str, content: str) -> AnalyzeResult:
        """Stage 3: Qualitaetsanalyse via aifw action_code=chapter_analyze."""
        ctx_block = self._get_context_block()
        style_block = self._get_style_constraints()

        try:
            messages = render_prompt(
                "authoring/chapter_analyze",
                ctx_block=ctx_block,
                style_block=style_block,
                content=content,
            )
            from promptfw.parsing import extract_json

            raw = self._router.completion(
                "chapter_analyze",
                messages,
                quality_level=self._quality_level,
                **{k: v for k, v in self._llm_overrides.items() if k == "model"},
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
            fixes = [i.get("description", "") for i in analyze.issues[:MAX_QUALITY_ISSUES]]
            return GateResult(decision="revise", allows_commit=False, required_fixes=fixes, reason=f"Score {score:.1f}")
        return GateResult(decision="reject", allows_commit=False, reason=f"Score {score:.1f} < 5.0")

    def produce_chapter(
        self,
        chapter_id: str,
        target_words: int = DEFAULT_TARGET_WORD_COUNT,
        max_iterations: int = 3,
        auto_commit: bool = False,
    ) -> ProductionResult:
        """Vollstaendige Pipeline ausfuehren."""
        start = time.time()
        brief_result = self.generate_brief(chapter_id)
        if not brief_result.success:
            return ProductionResult(
                success=False,
                stage=ProductionStage.BRIEF,
                chapter_id=chapter_id,
                brief=brief_result,
                error=brief_result.error,
                duration_seconds=time.time() - start,
            )

        write_result = None
        analyze_result = None
        gate_result = None

        for iteration in range(1, max_iterations + 1):
            write_result = self.write_chapter(chapter_id, brief_result.brief, target_words)
            if not write_result.success:
                return ProductionResult(
                    success=False,
                    stage=ProductionStage.WRITE,
                    chapter_id=chapter_id,
                    brief=brief_result,
                    write=write_result,
                    iterations=iteration,
                    error=write_result.error,
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
            stage=ProductionStage.COMMIT
            if (auto_commit and gate_result and gate_result.allows_commit)
            else ProductionStage.GATE,
            chapter_id=chapter_id,
            brief=brief_result,
            write=write_result,
            analyze=analyze_result,
            gate=gate_result,
            iterations=iteration,
            duration_seconds=time.time() - start,
        )


def get_chapter_production_service(
    project_id: str,
    user=None,
    llm_overrides: dict | None = None,
) -> ChapterProductionService:
    return ChapterProductionService(
        project_id=project_id,
        user=user,
        llm_overrides=llm_overrides,
    )
