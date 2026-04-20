"""
Outlines — Service Layer

Delegates to OutlineGeneratorService (→ outlinefw) for full generation,
and uses fieldprefill (ADR-107) for single-node AI enrichment.

Pattern: same as risk-hub ai_analysis/services.py — register retrievers
for existing content, call prefill_fields() with context, map results back.

Extracted from views.py per platform service-layer convention (ADR-041).
"""

import logging

from apps.projects.constants import FORMAT_PROFILES, TENSION_TO_ARC
from apps.projects.models import OutlineNode, OutlineVersion

logger = logging.getLogger(__name__)


class OutlineGenerationService:
    """Generates and enriches outline nodes via outlinefw (SSoT)."""

    def generate_full(
        self,
        outline: OutlineVersion,
        detail_level: str = "full",
    ) -> dict:
        """
        Generate outline via outlinefw and map results onto existing DB nodes.

        Delegates to OutlineGeneratorService which wraps outlinefw.OutlineGenerator.
        Maps generated nodes (beat_name, act, summary, tension) back to
        existing DB OutlineNodes.

        Returns:
            {"updated": int, "total": int, "errors": list[str]}
        """
        from apps.authoring.services.outline_service import OutlineGeneratorService

        project = outline.project
        nodes = list(outline.nodes.order_by("order"))
        if not nodes:
            return {"updated": 0, "total": 0, "errors": ["Keine Kapitel vorhanden."]}

        total = len(nodes)
        errors = []

        # Generate via outlinefw (SSoT for outline generation)
        svc = OutlineGeneratorService()
        result = svc.generate_outline(
            project_id=str(project.pk),
            framework=outline.source or "three_act",
            chapter_count=total,
            quality="standard",
        )

        if not result.success:
            msg = getattr(result, "error_message", str(result))
            logger.warning("outlinefw generation failed: %s", msg)
            errors.append(f"outlinefw: {msg}")
            return {"updated": 0, "total": total, "errors": errors}

        # Map outlinefw nodes → existing DB nodes by position order
        generated = getattr(result, "nodes", []) or []
        updated = 0

        for i, node in enumerate(nodes):
            if i >= len(generated):
                break
            gen = generated[i]
            try:
                # Map outlinefw fields to DB fields
                beat_name = getattr(gen, "beat_name", "") or ""
                act_val = getattr(gen, "act", "")
                if hasattr(act_val, "value"):
                    act_val = act_val.value
                summary = getattr(gen, "summary", "") or ""
                tension = getattr(gen, "tension", "")
                if hasattr(tension, "value"):
                    tension = tension.value
                key_events = getattr(gen, "key_events", []) or []

                node.beat_phase = beat_name or node.beat_phase
                node.act = str(act_val) if act_val else node.act

                # Enrich description with summary + key events
                if detail_level in ("full", "detail") and summary:
                    desc_parts = [summary]
                    if key_events:
                        desc_parts.append("\n".join(f"• {e}" for e in key_events))
                    node.description = "\n\n".join(desc_parts)

                # Map tension → emotional_arc
                if tension:
                    arc = TENSION_TO_ARC.get(str(tension), str(tension))
                    node.emotional_arc = arc[:300]

                # Distribute target words evenly
                if project.target_word_count and not node.target_words:
                    node.target_words = project.target_word_count // total

                node.save(
                    update_fields=[
                        "beat_phase",
                        "act",
                        "description",
                        "emotional_arc",
                        "target_words",
                    ]
                )
                updated += 1
            except Exception as exc:
                logger.warning(
                    "generate_full: failed mapping node %s: %s",
                    node.order,
                    exc,
                )
                errors.append(f"Node {node.order}: {exc}")

        return {"updated": updated, "total": total, "errors": errors}

    def enrich_node(self, node: OutlineNode) -> dict:
        """
        AI-enrich a single outline node with detailed description.

        Uses DB-backed prompt templates (OutlinePromptTemplate) with
        content-type-aware dispatch (fiction/academic/nonfiction).
        Falls back to .jinja2 files if no DB template exists.

        Returns:
            {"success": True, "template_id": int|None} or
            {"success": False, "error": str}
        """
        from promptfw.parsing import extract_json

        from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError
        from apps.authoring.services.project_context_service import (
            ProjectContextService,
        )
        from apps.outlines.prompt_dispatch import (
            get_active_template,
            render_outline_prompt,
        )

        project = node.outline_version.project
        existing = node.description.strip() or "(noch kein Inhalt)"

        # Build context block from ProjectContextService
        try:
            ctx_svc = ProjectContextService()
            ctx = ctx_svc.get_context(str(project.pk))
            context_block = ctx.to_prompt_block()
        except Exception:
            context_block = f"Projekt: {project.title}\nGenre: {project.genre}"

        profile = FORMAT_PROFILES.get(project.content_type, {})

        try:
            prompt_msgs = render_outline_prompt(
                template_key="enrich_node",
                content_type=project.content_type,
                context_block=context_block,
                beat_phase=node.beat_phase or "",
                act=node.act or "",
                order=node.order,
                title=node.title,
                target_words=node.target_words or 3000,
                description=existing,
                quality_criteria=profile.get("quality_criteria", ""),
                outline_logic=profile.get("outline_logic", ""),
            )

            router = LLMRouter()
            raw = router.completion(
                action_code="chapter_outline",
                messages=prompt_msgs,
            )
            data = extract_json(raw)
            if data:
                node.description = data.get("description", raw)
                arc = data.get("emotional_arc", node.emotional_arc)
                node.emotional_arc = arc if arc else node.emotional_arc
            else:
                node.description = raw

            node.save(update_fields=["description", "emotional_arc"])

            # Track which template version was used (for quality feedback loop)
            active_tpl = get_active_template("enrich_node", project.content_type)
            tpl_id = active_tpl.pk if active_tpl else None

            logger.info("enrich_node ok node=%s tpl=%s", node.pk, tpl_id)
            return {"success": True, "template_id": tpl_id}
        except LLMRoutingError as exc:
            logger.warning("enrich_node LLM error node=%s: %s", node.pk, exc)
            return {"success": False, "error": f"KI nicht verfügbar: {exc}"}
        except Exception as exc:
            logger.exception("enrich_node error node=%s: %s", node.pk, exc)
            return {"success": False, "error": str(exc)}
