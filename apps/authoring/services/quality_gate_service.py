"""
QualityGateService — Business Logic für Quality Gate Evaluation.

Portiert aus bfagent.writing_hub.services.quality_gate_service (ADR-083).
Service-Layer-Pattern: views → services → models.
"""

import logging
from decimal import Decimal

from django.db import transaction

logger = logging.getLogger(__name__)


class QualityGateService:
    """
    Service für Quality Gate Evaluation.

    Verantwortlich für:
    - Berechnung gewichteter Scores
    - Gate-Entscheidungen basierend auf Konfiguration
    - Erstellen von ChapterQualityScore Records
    """

    def evaluate(
        self,
        chapter_ref: str,
        project_id: str,
        dimension_scores: dict[str, Decimal],
        findings: dict | None = None,
        user=None,
        notes: str = "",
    ):
        """
        Bewertet ein Kapitel und erstellt Score + Gate-Entscheidung.

        Args:
            chapter_ref: Externe Referenz auf das Kapitel (bfagent chapter ID)
            project_id: UUID des writing-hub BookProject
            dimension_scores: {'style': Decimal('8.5'), 'genre': Decimal('7.2'), ...}
            findings: Optionale strukturierte Findings
            user: Bewerter (User instance)
            notes: Optionale Notizen

        Returns:
            ChapterQualityScore mit Gate-Entscheidung
        """
        from apps.authoring.models import (
            ChapterDimensionScore,
            ChapterQualityScore,
            ProjectQualityConfig,
            QualityDimension,
        )
        from apps.projects.models import BookProject

        project = BookProject.objects.get(pk=project_id)
        config = self._get_or_create_config(project)

        overall = self._compute_weighted_score(dimension_scores)
        decision = self._compute_gate_decision(overall, dimension_scores, config)

        logger.info(
            "evaluate chapter_ref=%s overall=%s decision=%s",
            chapter_ref, overall, decision.code,
        )

        with transaction.atomic():
            score = ChapterQualityScore.objects.create(
                chapter_ref=chapter_ref,
                project=project,
                scored_by=user,
                gate_decision=decision,
                overall_score=overall,
                findings=findings or {},
                notes=notes,
            )

            dimensions = {
                d.code: d
                for d in QualityDimension.objects.filter(
                    code__in=dimension_scores.keys(), is_active=True
                )
            }
            for code, value in dimension_scores.items():
                if code in dimensions:
                    ChapterDimensionScore.objects.create(
                        quality_score=score,
                        dimension=dimensions[code],
                        score=value,
                    )
                else:
                    logger.warning("Unknown dimension code: %s", code)

        return score

    def _compute_weighted_score(self, scores: dict[str, Decimal]) -> Decimal:
        from apps.authoring.models import QualityDimension

        dimensions = QualityDimension.objects.filter(
            code__in=scores.keys(), is_active=True
        )
        total_weight = Decimal("0")
        weighted_sum = Decimal("0")

        for dim in dimensions:
            if dim.code in scores:
                weighted_sum += Decimal(str(scores[dim.code])) * dim.weight
                total_weight += dim.weight

        if total_weight == 0:
            return Decimal("0")
        return (weighted_sum / total_weight).quantize(Decimal("0.01"))

    def _compute_gate_decision(self, overall: Decimal, scores: dict[str, Decimal], config):
        from apps.authoring.models import GateDecisionType

        if overall < config.auto_reject_threshold:
            return GateDecisionType.objects.get(code="reject")
        if overall < config.min_overall_score:
            return GateDecisionType.objects.get(code="revise")
        if overall >= config.auto_approve_threshold and not config.require_manual_approval:
            return GateDecisionType.objects.get(code="approve")
        return GateDecisionType.objects.get(code="review")

    def _get_or_create_config(self, project):
        from apps.authoring.models import ProjectQualityConfig

        config, created = ProjectQualityConfig.objects.get_or_create(project=project)
        if created:
            logger.info("Created default quality config for project %s", project.pk)
        return config

    def get_latest_score(self, chapter_ref: str):
        from apps.authoring.models import ChapterQualityScore

        return (
            ChapterQualityScore.objects.filter(chapter_ref=chapter_ref)
            .select_related("gate_decision")
            .prefetch_related("dimension_scores__dimension")
            .order_by("-scored_at")
            .first()
        )

    def can_commit_chapter(self, chapter_ref: str) -> tuple[bool, str]:
        latest = self.get_latest_score(chapter_ref)
        if not latest:
            return False, "Kein Quality Score vorhanden"
        if not latest.gate_decision.allows_commit:
            return False, f"Gate-Entscheidung '{latest.gate_decision.name_de}' erlaubt keinen Commit"
        return True, "OK"


quality_gate_service = QualityGateService()
