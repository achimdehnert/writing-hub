"""
Authoring Celery Tasks — writing-hub (ADR-083 Phase 3)

Async Kapitel-Generierung: kein asyncio.run() im Request-Handler.
Flow: View → write_chapter_task.delay() → Polling-API → Ergebnis
"""

import logging

import structlog
from celery import shared_task

logger = structlog.get_logger(__name__)


@shared_task(
    bind=True,
    max_retries=1,
    default_retry_delay=30,
    name="authoring.write_chapter",
)
def write_chapter_task(
    self,
    project_id: str,
    chapter_ref: str,
    chapter_number: int = 1,
    chapter_title: str = "",
    chapter_outline: str = "",
    target_word_count: int = 2000,
    chapter_beat: str = "",
    emotional_arc: str = "",
    prev_chapter_summary: str = "",
) -> dict:
    """
    Celery Task: Kapitel asynchron generieren.

    Flow:
        1. View erstellt ChapterWriteJob(status='pending')
        2. View startet write_chapter_task.delay(...)
        3. Task ruft ChapterWriterHandler.write_chapter() auf
        4. Job-Status → 'done' / 'failed'
        5. Polling: GET /authoring/jobs/<job_id>/status/ → JSON
    """
    from apps.authoring.handlers.chapter_writer_handler import (
        ChapterContext,
        ChapterWriterHandler,
    )
    from apps.authoring.models_jobs import ChapterWriteJob

    log = logger.bind(task_id=self.request.id, chapter_ref=chapter_ref)
    log.info("write_chapter_task_started")

    try:
        job = ChapterWriteJob.objects.get(chapter_ref=chapter_ref, project_id=project_id)
    except ChapterWriteJob.DoesNotExist:
        log.error("job_not_found")
        return {"status": "error", "reason": "Job not found"}

    try:
        context = ChapterContext.from_project(
            project_id=project_id,
            chapter_ref=chapter_ref,
        )
        context.chapter_number = chapter_number
        context.chapter_title = chapter_title
        context.chapter_outline = chapter_outline
        context.target_word_count = target_word_count
        context.chapter_beat = chapter_beat
        context.emotional_arc = emotional_arc
        context.prev_chapter_summary = prev_chapter_summary

        handler = ChapterWriterHandler()
        result = handler.write_chapter(context)

        if result.get("success"):
            job.status = "done"
            job.content = result["content"]
            job.word_count = result.get("word_count", 0)
            job.save(update_fields=["status", "content", "word_count"])
            log.info("write_chapter_task_done", word_count=result.get("word_count"))
            return {"status": "done", "word_count": result["word_count"]}

        job.status = "failed"
        job.error = result.get("error", "Unknown error")
        job.save(update_fields=["status", "error"])
        log.error("write_chapter_task_failed", error=job.error)
        return {"status": "failed", "error": job.error}

    except Exception as exc:
        log.error("write_chapter_task_exception", error=str(exc))
        try:
            job.status = "failed"
            job.error = str(exc)
            job.save(update_fields=["status", "error"])
        except Exception:
            pass
        raise self.retry(exc=exc)
