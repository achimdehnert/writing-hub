"""
Authoring Celery Tasks — writing-hub (ADR-083 Phase 3)

Async Kapitel-Generierung: kein asyncio.run() im Request-Handler.
Flow: View → write_chapter_task.delay() → Polling-API → Ergebnis
"""

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


@shared_task(
    bind=True,
    max_retries=2,
    soft_time_limit=3600,
    name="authoring.run_batch_write",
)
def run_batch_write(self, job_id: str) -> dict:
    """
    Celery Task: Sequenzielle Batch-Generierung mehrerer Kapitel (ADR-161).

    Sequenziell — jedes Kapitel bekommt den Inhalt des vorherigen als Kontext.
    Sicherheits-Limit: max_chapters=10 pro Job.
    """
    from apps.authoring.models_jobs import BatchWriteJob
    from apps.projects.models import OutlineNode

    log = logger.bind(task_id=self.request.id, job_id=job_id)
    log.info("run_batch_write_started")

    try:
        job = BatchWriteJob.objects.select_related("project").get(id=job_id)
    except BatchWriteJob.DoesNotExist:
        log.error("batch_job_not_found")
        return {"status": "error", "reason": "Job not found"}

    job.status = "running"
    job.save(update_fields=["status", "updated_at"])

    node_ids = (job.node_ids or [])[:job.max_chapters]
    prev_content = ""

    for i, node_id in enumerate(node_ids):
        job.current_index = i
        job.save(update_fields=["current_index", "updated_at"])
        try:
            node = OutlineNode.objects.get(id=node_id)
            from apps.authoring.handlers.chapter_writer_handler import (
                ChapterContext,
                ChapterWriterHandler,
            )
            context = ChapterContext.from_project(
                project_id=str(job.project.id),
                chapter_ref=str(node.id),
            )
            context.chapter_number = node.order
            context.chapter_title = node.title
            context.chapter_outline = node.description or ""
            context.target_word_count = node.target_words or 2000
            context.chapter_beat = node.beat_phase or ""
            context.emotional_arc = node.emotional_arc or ""
            context.prev_chapter_summary = prev_content[-800:]

            handler = ChapterWriterHandler()
            result = handler.write_chapter(context)

            if result.get("success"):
                content = result["content"]
                node.content = content
                node.save(update_fields=["content", "content_updated_at"])
                prev_content = content
                job.completed_count += 1
            else:
                job.failed_count += 1
                job.error_log.append({
                    "index": i,
                    "node_id": node_id,
                    "error": result.get("error", "Unknown error"),
                })
        except Exception as exc:
            log.error("batch_chapter_failed", index=i, node_id=node_id, error=str(exc))
            job.failed_count += 1
            job.error_log.append({"index": i, "node_id": node_id, "error": str(exc)})

        job.save(update_fields=["completed_count", "failed_count", "error_log", "updated_at"])

    job.status = "done" if job.failed_count == 0 else "failed"
    job.save(update_fields=["status", "updated_at"])
    log.info("run_batch_write_finished", status=job.status, completed=job.completed_count)
    return {"status": job.status, "completed": job.completed_count, "failed": job.failed_count}


@shared_task(
    bind=True,
    max_retries=1,
    soft_time_limit=7200,
    name="authoring.run_essay_pipeline",
)
def run_essay_pipeline(self, job_id: str) -> dict:
    """
    Celery Task: Autonome Essay-Pipeline (Quick Project).

    Steps: Outline → Recherche → Schreiben → Peer Review
    Progress-Tracking via EssayPipelineJob.
    """
    from apps.authoring.models_jobs import EssayPipelineJob

    log = logger.bind(task_id=self.request.id, job_id=job_id)
    log.info("essay_pipeline_started")

    try:
        job = EssayPipelineJob.objects.select_related("project", "requested_by").get(id=job_id)
    except EssayPipelineJob.DoesNotExist:
        log.error("essay_pipeline_job_not_found")
        return {"status": "error", "reason": "Job not found"}

    project = job.project
    user = job.requested_by

    try:
        job.status = "running"
        job.save(update_fields=["status", "updated_at"])

        # ── Step 1: Outline ───────────────────────────────────────
        job.current_step = "outline"
        job.save(update_fields=["current_step", "updated_at"])
        job.add_log("Outline wird generiert...")

        nodes = _pipeline_generate_outline(project, user, job)
        if not nodes:
            job.status = "failed"
            job.current_step = "failed"
            job.error = "Outline-Generierung fehlgeschlagen"
            job.save(update_fields=["status", "current_step", "error", "updated_at"])
            return {"status": "failed", "error": job.error}

        job.total_chapters = len(nodes)
        job.completed_chapters = 0
        job.add_log(f"{len(nodes)} Kapitel im Outline")

        # ── Step 2: Recherche ─────────────────────────────────────
        if job.do_research:
            job.current_step = "research"
            job.completed_chapters = 0
            job.save(update_fields=["current_step", "completed_chapters", "updated_at"])
            job.add_log("Literaturrecherche gestartet...")
            _pipeline_research(project, nodes, job)

        # ── Step 3: Schreiben ─────────────────────────────────────
        job.current_step = "writing"
        job.completed_chapters = 0
        job.save(update_fields=["current_step", "completed_chapters", "updated_at"])
        job.add_log("Kapitel werden geschrieben...")
        _pipeline_write_chapters(project, user, nodes, job)

        # ── Step 4: Peer Review ───────────────────────────────────
        if job.do_review:
            job.current_step = "review"
            job.save(update_fields=["current_step", "updated_at"])
            job.add_log("Peer Review gestartet...")
            _pipeline_peer_review(project, user, job)

        # ── Done ──────────────────────────────────────────────────
        job.status = "done"
        job.current_step = "done"
        total_words = sum(n.word_count for n in project.outline_versions.filter(
            is_active=True
        ).first().nodes.all()) if project.outline_versions.filter(is_active=True).exists() else 0
        job.add_log(f"Fertig! {total_words:,} Woerter geschrieben.")
        job.save(update_fields=["status", "current_step", "updated_at"])
        log.info("essay_pipeline_done", total_words=total_words)
        return {"status": "done", "total_words": total_words}

    except Exception as exc:
        log.error("essay_pipeline_exception", error=str(exc))
        job.status = "failed"
        job.current_step = "failed"
        job.error = str(exc)
        job.add_log(f"Fehler: {exc}")
        job.save(update_fields=["status", "current_step", "error", "updated_at"])
        return {"status": "failed", "error": str(exc)}


def _pipeline_generate_outline(project, user, job):
    """Generate outline for the essay pipeline."""
    from apps.authoring.services.outline_service import OutlineGeneratorService
    from apps.projects.models import OutlineFramework, OutlineNode, OutlineVersion

    svc = OutlineGeneratorService()
    framework = job.framework

    try:
        result = svc.generate_outline(
            project_id=str(project.pk),
            framework=framework,
            chapter_count=12,
            quality="standard",
        )
        if result.success and result.nodes:
            version_id = svc.save_outline(
                project_id=str(project.pk),
                nodes=result.nodes,
                name=f"Quick-Essay: {framework}",
                framework=framework,
                user=user,
            )
            if version_id:
                version = OutlineVersion.objects.get(pk=version_id)
                nodes = list(version.nodes.order_by("order"))
                if nodes and project.target_word_count:
                    words_per = project.target_word_count // len(nodes)
                    for node in nodes:
                        if not node.target_words:
                            node.target_words = words_per
                            node.save(update_fields=["target_words"])
                return nodes
    except Exception as exc:
        job.add_log(f"KI-Outline fehlgeschlagen: {exc}")

    # Fallback: Framework-Beats oder generische Kapitel
    job.add_log("Verwende Framework-Beats als Fallback")
    OutlineVersion.objects.filter(project=project, is_active=True).update(is_active=False)
    version = OutlineVersion.objects.create(
        project=project,
        created_by=user,
        name=f"Essay: {framework}",
        source=framework,
        is_active=True,
    )
    fw_obj = OutlineFramework.objects.filter(key=framework).first()
    if fw_obj:
        beats = list(fw_obj.beats.order_by("order"))
        if beats:
            words_per = (project.target_word_count or 5000) // len(beats)
            OutlineNode.objects.bulk_create([
                OutlineNode(
                    outline_version=version,
                    title=b.name,
                    description=b.description,
                    beat_type="chapter",
                    beat_phase=b.name,
                    target_words=words_per,
                    order=b.order,
                )
                for b in beats
            ])
            return list(version.nodes.order_by("order"))

    # Ultra-Fallback
    words_per = (project.target_word_count or 5000) // 5
    OutlineNode.objects.bulk_create([
        OutlineNode(
            outline_version=version, title=t,
            beat_type="chapter", target_words=words_per, order=i + 1,
        )
        for i, t in enumerate([
            "Einleitung", "Theoretischer Rahmen", "Methodik",
            "Ergebnisse & Analyse", "Fazit & Ausblick",
        ])
    ])
    return list(version.nodes.order_by("order"))


def _pipeline_research(project, nodes, job):
    """Run literature research for each chapter."""
    from django.conf import settings as django_settings

    from apps.projects.services.citation_service import research_outline_node

    llm_key = getattr(django_settings, "TOGETHER_API_KEY", "")
    project_topic = project.description or project.title

    for i, node in enumerate(nodes):
        job.current_chapter_title = node.title
        job.completed_chapters = i
        job.save(update_fields=["current_chapter_title", "completed_chapters", "updated_at"])
        try:
            result = research_outline_node(
                node_title=node.title,
                node_description=node.description or "",
                target_words=node.target_words,
                project_topic=project_topic,
                style="scientific",
                llm_api_key=llm_key or None,
            )
            paper_count = len(result.get("papers", []))
            brief = result.get("writing_brief", "")
            if brief and node.description:
                node.notes = f"## Recherche-Ergebnis\n\n{brief}\n\n---\nQuellen: {paper_count} Papers"
            elif brief:
                node.description = brief
                node.notes = f"Quellen: {paper_count} Papers"
            node.save(update_fields=["description", "notes"])
            job.add_log(f"Recherche {node.title}: {paper_count} Papers")
        except Exception as exc:
            job.add_log(f"Recherche {node.title}: Fehler ({exc})")

    job.completed_chapters = len(nodes)
    job.save(update_fields=["completed_chapters", "updated_at"])


def _pipeline_write_chapters(project, user, nodes, job):
    """Write all chapters using ChapterProductionService or ChapterWriterHandler."""
    from apps.authoring.handlers.chapter_writer_handler import (
        ChapterContext,
        ChapterWriterHandler,
    )

    prev_content = ""
    for i, node in enumerate(nodes):
        job.current_chapter_title = node.title
        job.completed_chapters = i
        job.save(update_fields=["current_chapter_title", "completed_chapters", "updated_at"])

        try:
            context = ChapterContext.from_project(
                project_id=str(project.pk),
                chapter_ref=str(node.pk),
            )
            context.chapter_number = node.order
            context.chapter_title = node.title
            context.chapter_outline = node.description or ""
            context.target_word_count = node.target_words or 2000
            context.chapter_beat = node.beat_phase or ""
            context.emotional_arc = node.emotional_arc or ""
            context.prev_chapter_summary = prev_content[-800:] if prev_content else ""

            handler = ChapterWriterHandler()
            result = handler.write_chapter(context)

            if result.get("success"):
                content = result["content"]
                node.content = content
                node.save(update_fields=["content", "word_count", "content_updated_at"])
                prev_content = content
                wc = node.word_count
                job.add_log(f"Kapitel {node.order}. {node.title}: {wc} Woerter")
            else:
                job.add_log(f"Kapitel {node.order}. {node.title}: Fehler ({result.get('error', '?')})")
        except Exception as exc:
            job.add_log(f"Kapitel {node.order}. {node.title}: Fehler ({exc})")

    job.completed_chapters = len(nodes)
    job.save(update_fields=["completed_chapters", "updated_at"])


def _pipeline_peer_review(project, user, job):
    """Run peer review on the completed essay."""
    try:
        from apps.projects.services.peer_review_service import run_peer_review
        session_id = run_peer_review(project, user)
        if session_id:
            job.add_log(f"Peer Review abgeschlossen (Session {session_id})")
        else:
            job.add_log("Peer Review: kein Ergebnis (keine Kapitel mit Inhalt?)")
    except Exception as exc:
        job.add_log(f"Peer Review: Fehler ({exc})")
