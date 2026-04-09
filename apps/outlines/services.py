"""
Outlines — Service Layer

Delegates to OutlineGeneratorService (→ outlinefw) for full generation,
and uses fieldprefill (ADR-107) for single-node AI enrichment.

Pattern: same as risk-hub ai_analysis/services.py — register retrievers
for existing content, call prefill_fields() with context, map results back.

Extracted from views.py per platform service-layer convention (ADR-041).
"""
import logging

from apps.projects.models import OutlineNode, OutlineVersion

logger = logging.getLogger(__name__)


# outlinefw node field → DB OutlineNode field mapping
_TENSION_TO_ARC = {
    "low": "ruhig / reflektiv",
    "medium": "aufbauend",
    "high": "intensiv / spannend",
    "peak": "Höhepunkt / Klimax",
}


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
                        desc_parts.append(
                            "\n".join(f"• {e}" for e in key_events)
                        )
                    node.description = "\n\n".join(desc_parts)

                # Map tension → emotional_arc
                if tension:
                    arc = _TENSION_TO_ARC.get(str(tension), str(tension))
                    node.emotional_arc = arc[:300]

                # Distribute target words evenly
                if project.target_word_count and not node.target_words:
                    node.target_words = project.target_word_count // total

                node.save(update_fields=[
                    "beat_phase", "act", "description",
                    "emotional_arc", "target_words",
                ])
                updated += 1
            except Exception as exc:
                logger.warning(
                    "generate_full: failed mapping node %s: %s",
                    node.order, exc,
                )
                errors.append(f"Node {node.order}: {exc}")

        return {"updated": updated, "total": total, "errors": errors}

    def enrich_node(self, node: OutlineNode) -> dict:
        """
        AI-enrich a single outline node with detailed description.

        Uses fieldprefill (ADR-107) with registered retrievers for
        project context and sibling nodes. Same pattern as risk-hub
        ai_analysis/services.py — gather context, call LLM, map results.

        Returns:
            {"success": True} or {"success": False, "error": str}
        """
        from fieldprefill import prefill_fields

        project = node.outline_version.project
        existing = node.description.strip() or "(noch kein Inhalt)"

        try:
            result = prefill_fields(
                field_keys=["description", "emotional_arc"],
                prompt=(
                    f"Kapitel {node.order}: {node.title}\n"
                    f"Beat/Phase: {node.beat_phase or 'k.A.'}\n"
                    f"Akt: {node.act or 'k.A.'}\n"
                    f"Ziel-Wörter: {node.target_words or 3000}\n\n"
                    f"Bisheriger Inhalt:\n{existing}\n\n"
                    "Erstelle ein DETAILLIERTES Kapitel-Outline mit 2-4 Szenen, "
                    "Dialog-Hinweisen, innerem Monolog und Cliffhanger."
                ),
                action_code="chapter_outline",
                sources=["project_context", "outline_siblings"],
                context={
                    "beat_phase": node.beat_phase or "",
                    "act": node.act or "",
                    "title": node.title,
                    "order": str(node.order),
                },
                scope="writing.outline_enrichment",
                tenant_id=project.owner_id,
                instance=project,
                max_tokens=2048,
            )

            if result.error:
                logger.warning("enrich_node prefill error node=%s: %s", node.pk, result.error)
                return {"success": False, "error": f"KI nicht verfügbar: {result.error}"}

            # Map structured JSON fields back to DB
            data = result.as_dict()
            if data:
                node.description = data.get("description", result.content)
                arc = data.get("emotional_arc", node.emotional_arc)
                node.emotional_arc = arc[:300] if arc else node.emotional_arc
            else:
                node.description = result.content

            node.save(update_fields=["description", "emotional_arc"])
            logger.info(
                "enrich_node ok node=%s model=%s tokens=%d latency=%dms",
                node.pk, result.model, result.tokens_used, result.latency_ms,
            )
            return {"success": True}
        except Exception as exc:
            logger.exception("enrich_node error node=%s: %s", node.pk, exc)
            return {"success": False, "error": str(exc)}
