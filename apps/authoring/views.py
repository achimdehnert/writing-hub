"""
Authoring API Views — writing-hub (ADR-083 Phase 3)

Service-Layer-Pattern: views → services/handlers → models.
Async-Pattern: POST start → Celery Task → GET status polling.
"""

import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class chapter_write_start(APIView):
    """
    POST /authoring/projects/<project_id>/chapters/<chapter_ref>/write/

    Startet async Kapitel-Generierung.
    Erstellt ChapterWriteJob + startet Celery Task.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id, chapter_ref):
        from apps.authoring.models_jobs import ChapterWriteJob
        from apps.authoring.tasks import write_chapter_task
        from apps.projects.models import BookProject

        try:
            project = BookProject.objects.get(pk=project_id, owner=request.user)
        except BookProject.DoesNotExist:
            return Response({"detail": "Projekt nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        existing = ChapterWriteJob.objects.filter(
            project=project,
            chapter_ref=str(chapter_ref),
            status__in=["pending", "running"],
        ).first()
        if existing:
            return Response(
                {"job_id": str(existing.id), "status": existing.status, "detail": "Job läuft bereits."},
                status=status.HTTP_202_ACCEPTED,
            )

        data = request.data
        job = ChapterWriteJob.objects.create(
            project=project,
            chapter_ref=str(chapter_ref),
            requested_by=request.user,
            status="pending",
        )

        write_chapter_task.delay(
            project_id=str(project_id),
            chapter_ref=str(chapter_ref),
            chapter_number=data.get("chapter_number", 1),
            chapter_title=data.get("chapter_title", ""),
            chapter_outline=data.get("chapter_outline", ""),
            target_word_count=data.get("target_word_count", 2000),
            chapter_beat=data.get("chapter_beat", ""),
            emotional_arc=data.get("emotional_arc", ""),
            prev_chapter_summary=data.get("prev_chapter_summary", ""),
        )

        return Response(
            {"job_id": str(job.id), "status": "pending"},
            status=status.HTTP_202_ACCEPTED,
        )


class chapter_write_status(APIView):
    """
    GET /authoring/jobs/<job_id>/status/

    Polling-Endpunkt für Kapitel-Generierung.
    Response: {status, content?, word_count?, error?}
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        from apps.authoring.models_jobs import ChapterWriteJob

        try:
            job = ChapterWriteJob.objects.get(pk=job_id, requested_by=request.user)
        except ChapterWriteJob.DoesNotExist:
            return Response({"detail": "Job nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        payload = {"status": job.status, "job_id": str(job.id)}
        if job.is_done:
            payload["content"] = job.content
            payload["word_count"] = job.word_count
        elif job.is_failed:
            payload["error"] = job.error

        return Response(payload)


class chapter_quality_score(APIView):
    """
    GET  /authoring/projects/<project_id>/chapters/<chapter_ref>/quality/
    POST /authoring/projects/<project_id>/chapters/<chapter_ref>/quality/

    GET:  Letzten Quality Score abrufen.
    POST: Neuen Score erstellen (dimension_scores im Body).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id, chapter_ref):
        from apps.authoring.services.quality_gate_service import quality_gate_service

        score = quality_gate_service.get_latest_score(str(chapter_ref))
        if not score:
            return Response({"detail": "Kein Score vorhanden."}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "chapter_ref": score.chapter_ref,
            "overall_score": str(score.overall_score),
            "gate_decision": score.gate_decision.code,
            "allows_commit": score.gate_decision.allows_commit,
            "scored_at": score.scored_at.isoformat(),
            "dimensions": [
                {"code": ds.dimension.code, "score": str(ds.score)}
                for ds in score.dimension_scores.select_related("dimension").all()
            ],
        })

    def post(self, request, project_id, chapter_ref):
        from decimal import Decimal

        from apps.authoring.services.quality_gate_service import quality_gate_service

        raw_scores = request.data.get("dimension_scores", {})
        if not raw_scores:
            return Response(
                {"detail": "dimension_scores erforderlich."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            dimension_scores = {k: Decimal(str(v)) for k, v in raw_scores.items()}
        except Exception as exc:
            return Response(
                {"detail": f"Ungültige Scores: {exc}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        score = quality_gate_service.evaluate(
            chapter_ref=str(chapter_ref),
            project_id=str(project_id),
            dimension_scores=dimension_scores,
            findings=request.data.get("findings"),
            user=request.user,
            notes=request.data.get("notes", ""),
        )

        return Response(
            {
                "chapter_ref": score.chapter_ref,
                "overall_score": str(score.overall_score),
                "gate_decision": score.gate_decision.code,
                "allows_commit": score.gate_decision.allows_commit,
            },
            status=status.HTTP_201_CREATED,
        )
