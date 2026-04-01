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

        try:
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
        except Exception:
            logger.warning(
                "Celery nicht verfügbar — synchrone Generierung für chapter_ref=%s",
                chapter_ref,
            )
            from apps.authoring.handlers.chapter_writer_handler import (
                ChapterContext,
                ChapterWriterHandler,
            )
            try:
                context = ChapterContext.from_project(
                    project_id=str(project_id),
                    chapter_ref=str(chapter_ref),
                )
                context.chapter_number = data.get("chapter_number", 1)
                context.chapter_title = data.get("chapter_title", "")
                context.chapter_outline = data.get("chapter_outline", "")
                context.target_word_count = data.get("target_word_count", 2000)
                context.chapter_beat = data.get("chapter_beat", "")
                context.emotional_arc = data.get("emotional_arc", "")
                context.prev_chapter_summary = data.get("prev_chapter_summary", "")
                result = ChapterWriterHandler().write_chapter(context)
                if result.get("success"):
                    job.status = "done"
                    job.content = result["content"]
                    job.word_count = result.get("word_count", 0)
                    job.save(update_fields=["status", "content", "word_count"])
                else:
                    job.status = "failed"
                    job.error = result.get("error", "Generierung fehlgeschlagen")
                    job.save(update_fields=["status", "error"])
            except Exception as sync_exc:
                logger.exception("Synchrone Generierung fehlgeschlagen: %s", sync_exc)
                job.status = "failed"
                job.error = str(sync_exc)
                job.save(update_fields=["status", "error"])

        return Response(
            {"job_id": str(job.id), "status": job.status},
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


class OutlineGenerateView(APIView):
    """
    POST /authoring/projects/<project_id>/outline/generate/

    Gliederung via OutlineGeneratorService (aifw) generieren.
    Body: {genre, premise, chapter_count, style}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        from apps.authoring.services.outline_service import OutlineGeneratorService

        svc = OutlineGeneratorService(project_id=str(project_id))
        result = svc.generate_outline(
            genre=request.data.get("genre", ""),
            premise=request.data.get("premise", ""),
            chapter_count=int(request.data.get("chapter_count", 12)),
            style=request.data.get("style", ""),
        )
        if not result.success:
            return Response({"detail": result.error}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({
            "title": result.title,
            "premise": result.premise,
            "acts": result.acts,
            "beats": result.beats,
        }, status=status.HTTP_201_CREATED)


class OutlineBeatExpandView(APIView):
    """
    POST /authoring/projects/<project_id>/outline/beat/<beat_id>/expand/

    Einzelnen Beat via LLM vertiefen.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id, beat_id):
        from apps.authoring.services.outline_service import OutlineGeneratorService

        svc = OutlineGeneratorService(project_id=str(project_id))
        expanded = svc.expand_beat(
            beat_id=str(beat_id),
            context=request.data.get("context", ""),
        )
        if not expanded:
            return Response({"detail": "Beat konnte nicht erweitert werden."}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({"beat_id": beat_id, "expanded": expanded})


class IdeaGenerateView(APIView):
    """
    POST /authoring/ideas/generate/

    Buch-Ideen via IdeaGeneratorService (aifw) generieren.
    Body: {genre, keywords, count}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.idea_import.services.idea_service import IdeaGeneratorService

        svc = IdeaGeneratorService()
        result = svc.generate_ideas(
            genre=request.data.get("genre", ""),
            keywords=request.data.get("keywords", []),
            count=int(request.data.get("count", 5)),
        )
        if not result.success:
            return Response({"detail": result.error}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({"ideas": result.ideas}, status=status.HTTP_201_CREATED)


class IdeaToPremiseView(APIView):
    """
    POST /authoring/ideas/<idea_id>/to-premise/

    Rohe Idee in strukturiertes Premise umwandeln.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, idea_id):
        from apps.idea_import.models import IdeaCapture
        from apps.idea_import.services.idea_service import IdeaGeneratorService

        try:
            idea = IdeaCapture.objects.get(pk=idea_id, submitted_by=request.user)
        except IdeaCapture.DoesNotExist:
            return Response({"detail": "Idee nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        svc = IdeaGeneratorService()
        result = svc.idea_to_premise(raw_idea=idea.raw_text)
        if not result.success:
            return Response({"detail": result.error}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({
            "idea_id": str(idea_id),
            "premise": result.premise,
            "genre": result.genre,
            "themes": result.themes,
            "protagonist": result.protagonist,
        }, status=status.HTTP_201_CREATED)
