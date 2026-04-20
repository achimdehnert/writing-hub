"""
Management Command: write_essay — Autonome wissenschaftliche Aufsatz-Pipeline.

Orchestriert die gesamte writing-hub Pipeline Ende-zu-Ende:
  1. Projekt anlegen (BookProject, content_type=academic/scientific)
  2. Outline generieren (OutlineGeneratorService + outlinefw)
  3. Pro Kapitel recherchieren (researchfw: arXiv, Semantic Scholar, PubMed)
  4. Pro Kapitel schreiben (ChapterProductionService: Brief→Write→Analyze→Gate)
  5. Peer Review durchführen (4 Agenten: Methodik, Argumentation, Quellen, Struktur)
  6. Ergebnis-URL ausgeben

Usage:
    python manage.py write_essay \
        --title "KI in der Baubranche" \
        --topic "Analyse von LLM-Einsatz für BIM, Ausschreibung und Bauleitung" \
        --framework academic_essay \
        --target-words 5000 \
        --research \
        --peer-review

Das Projekt ist danach in der Web-UI unter /projekte/<id>/ bearbeitbar.
"""

import logging
import time

from django.conf import settings
from apps.authoring.defaults import (
    DEFAULT_CONTENT_TYPE,
    DEFAULT_FRAMEWORK,
    DEFAULT_PROJECT_TARGET_WORDS,
    DEFAULT_TARGET_WORD_COUNT,
)
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)

User = get_user_model()

FRAMEWORK_CHOICES = [
    "academic_essay",
    "scientific_essay",
    "imrad_article",
    "essay",
    "three_act",
]

CONTENT_TYPE_MAP = {
    "academic_essay": "academic",
    "scientific_essay": "scientific",
    "imrad_article": "scientific",
    "essay": "essay",
    "three_act": DEFAULT_CONTENT_TYPE,
}


class Command(BaseCommand):
    help = "Autonome wissenschaftliche Aufsatz-Pipeline: Outline → Recherche → Schreiben → Review"

    def add_arguments(self, parser):
        parser.add_argument(
            "--title",
            required=True,
            help="Titel des Aufsatzes",
        )
        parser.add_argument(
            "--topic",
            default="",
            help="Thema / Abstract / Forschungsfrage (wird als Projektbeschreibung gespeichert)",
        )
        parser.add_argument(
            "--framework",
            default=DEFAULT_FRAMEWORK,
            choices=FRAMEWORK_CHOICES,
            help=f"Outline-Framework (default: {DEFAULT_FRAMEWORK})",
        )
        parser.add_argument(
            "--target-words",
            type=int,
            default=DEFAULT_PROJECT_TARGET_WORDS,
            help=f"Ziel-Wortanzahl gesamt (default: {DEFAULT_PROJECT_TARGET_WORDS})",
        )
        parser.add_argument(
            "--chapter-count",
            type=int,
            default=0,
            help="Anzahl Kapitel (0 = Framework-Standard)",
        )
        parser.add_argument(
            "--owner",
            default="",
            help="Owner: username oder email (default: erster Superuser)",
        )
        parser.add_argument(
            "--quality",
            default="standard",
            choices=["fast", "standard", "premium"],
            help="LLM-Qualität: fast=gpt-4o-mini/4k, standard=gpt-4o-mini/8k, premium=gpt-4o/16k",
        )
        parser.add_argument(
            "--research",
            action="store_true",
            help="Literaturrecherche pro Kapitel durchführen (researchfw)",
        )
        parser.add_argument(
            "--peer-review",
            action="store_true",
            help="Wissenschaftliches Peer Review nach dem Schreiben",
        )
        parser.add_argument(
            "--skip-write",
            action="store_true",
            help="Nur Outline + Recherche, kein Kapitel-Schreiben",
        )
        parser.add_argument(
            "--max-iterations",
            type=int,
            default=2,
            help="Max Write→Analyze→Revise Iterationen pro Kapitel (default: 2)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Nur Plan anzeigen, nichts ausführen",
        )

    def handle(self, *args, **options):
        start_time = time.time()
        title = options["title"]
        topic = options["topic"]
        framework = options["framework"]
        target_words = options["target_words"]
        chapter_count = options["chapter_count"]
        do_research = options["research"]
        do_review = options["peer_review"]
        skip_write = options["skip_write"]
        max_iterations = options["max_iterations"]
        dry_run = options["dry_run"]

        self.stdout.write(self.style.MIGRATE_HEADING(f"\n{'=' * 60}\n  AUTONOME ESSAY-PIPELINE\n{'=' * 60}"))
        self.stdout.write(f"  Titel:       {title}")
        self.stdout.write(f"  Thema:       {topic or '(aus Titel abgeleitet)'}")
        self.stdout.write(f"  Framework:   {framework}")
        self.stdout.write(f"  Zielwörter:  {target_words:,}")
        self.stdout.write(f"  Recherche:   {'✓' if do_research else '✗'}")
        self.stdout.write(f"  Peer Review: {'✓' if do_review else '✗'}")
        self.stdout.write(f"  Schreiben:   {'✗ (skip)' if skip_write else '✓'}")
        self.stdout.write("")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — keine Änderungen."))
            return

        quality = options["quality"]

        # ── Step 0: User resolven ─────────────────────────────────
        user = self._resolve_user(options["owner"])
        self.stdout.write(f"  Owner:       {user.username} ({user.email})")
        llm_overrides = self._build_llm_overrides(quality)
        self.stdout.write(f"  Qualität:    {quality}")
        if llm_overrides:
            self.stdout.write(f"  LLM:         {llm_overrides}")

        # ── Step 1: Projekt anlegen ───────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING("\n[1/6] Projekt anlegen..."))
        project = self._create_project(user, title, topic, framework, target_words)
        self.stdout.write(self.style.SUCCESS(f"  ✓ Projekt erstellt: {project.pk}"))

        # ── Step 2: Outline generieren ────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING("\n[2/6] Outline generieren..."))
        outline, nodes = self._generate_outline(project, user, framework, chapter_count)
        if not nodes:
            raise CommandError("Outline-Generierung fehlgeschlagen — keine Kapitel erzeugt.")
        self.stdout.write(self.style.SUCCESS(f"  ✓ {len(nodes)} Kapitel generiert"))
        for node in nodes:
            words = node.target_words or "—"
            self.stdout.write(f"    {node.order}. {node.title} ({words} Wörter)")

        # ── Step 3: Recherche ─────────────────────────────────────
        if do_research:
            self.stdout.write(self.style.MIGRATE_HEADING("\n[3/6] Literaturrecherche..."))
            self._research_chapters(project, nodes)
        else:
            self.stdout.write(self.style.MIGRATE_HEADING("\n[3/6] Recherche übersprungen"))

        # ── Step 4: Kapitel schreiben ─────────────────────────────
        if not skip_write:
            self.stdout.write(self.style.MIGRATE_HEADING("\n[4/6] Kapitel schreiben..."))
            self._write_chapters(project, user, nodes, max_iterations, llm_overrides)
        else:
            self.stdout.write(self.style.MIGRATE_HEADING("\n[4/6] Schreiben übersprungen"))

        # ── Step 5: Peer Review ───────────────────────────────────
        if do_review and not skip_write:
            self.stdout.write(self.style.MIGRATE_HEADING("\n[5/6] Peer Review..."))
            self._run_peer_review(project, user)
        else:
            self.stdout.write(self.style.MIGRATE_HEADING("\n[5/6] Peer Review übersprungen"))

        # ── Step 6: Zusammenfassung ───────────────────────────────
        elapsed = time.time() - start_time
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n[6/6] Fertig! ({elapsed:.0f}s)"))
        self._print_summary(project, nodes, elapsed)

    # ── Helpers ────────────────────────────────────────────────────

    def _resolve_user(self, owner_ref: str):
        """Resolve user by username, email, or fall back to first superuser."""
        if owner_ref:
            # Try username first, then email
            user = User.objects.filter(username=owner_ref).first()
            if not user:
                user = User.objects.filter(email__iexact=owner_ref).first()
            if not user:
                raise CommandError(f"User '{owner_ref}' nicht gefunden (weder username noch email).")
            return user
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.first()
        if not user:
            raise CommandError("Kein User gefunden. Bitte --owner angeben.")
        return user

    def _build_llm_overrides(self, quality: str) -> dict:
        """Build per-call LLM overrides based on quality level.

        max_tokens is calculated dynamically from target_words in
        ChapterProductionService.write_chapter(), so we only need
        model overrides here for premium quality.
        """
        if quality == "premium":
            return {"model": "openai:gpt-4o"}
        return {}

    def _create_project(self, user, title, topic, framework, target_words):
        from apps.projects.models import BookProject, ContentTypeLookup

        content_type = CONTENT_TYPE_MAP.get(framework, "academic")

        ct_lookup = ContentTypeLookup.objects.filter(slug__in=["academic", "wissenschaftlich", "scientific"]).first()

        project = BookProject.objects.create(
            owner=user,
            title=title,
            description=topic or title,
            content_type=content_type,
            content_type_lookup=ct_lookup,
            target_word_count=target_words,
            is_active=True,
        )
        return project

    def _generate_outline(self, project, user, framework, chapter_count):
        from apps.authoring.services.outline_service import OutlineGeneratorService
        from apps.projects.models import OutlineVersion

        svc = OutlineGeneratorService()
        result = svc.generate_outline(
            project_id=str(project.pk),
            framework=framework,
            chapter_count=chapter_count or 12,
            quality="standard",
        )

        if result.success and result.nodes:
            version_id = svc.save_outline(
                project_id=str(project.pk),
                nodes=result.nodes,
                name=f"KI-Essay: {framework}",
                framework=framework,
                user=user,
            )
            if version_id:
                version = OutlineVersion.objects.get(pk=version_id)
                nodes = list(version.nodes.order_by("order"))
                # Zielwörter pro Kapitel verteilen falls nicht gesetzt
                if nodes and project.target_word_count:
                    words_per = project.target_word_count // len(nodes)
                    for node in nodes:
                        if not node.target_words:
                            node.target_words = words_per
                            node.save(update_fields=["target_words"])
                return version, nodes

        # Fallback: Manuelles Outline aus Framework-Beats
        self.stdout.write(self.style.WARNING("  ⚠ KI-Outline fehlgeschlagen, verwende Framework-Beats als Fallback"))
        if hasattr(result, "error_message") and result.error_message:
            self.stdout.write(f"    Grund: {result.error_message}")

        return self._create_fallback_outline(project, user, framework, chapter_count)

    def _create_fallback_outline(self, project, user, framework, chapter_count):
        from apps.projects.models import OutlineFramework, OutlineNode, OutlineVersion

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
                words_per = (project.target_word_count or DEFAULT_PROJECT_TARGET_WORDS) // len(beats)
                OutlineNode.objects.bulk_create(
                    [
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
                    ]
                )
                return version, list(version.nodes.order_by("order"))

        # Ultra-Fallback: generische Kapitel
        count = chapter_count or 5
        words_per = (project.target_word_count or DEFAULT_PROJECT_TARGET_WORDS) // count
        OutlineNode.objects.bulk_create(
            [
                OutlineNode(
                    outline_version=version,
                    title=t,
                    beat_type="chapter",
                    target_words=words_per,
                    order=i + 1,
                )
                for i, t in enumerate(
                    [
                        "Einleitung",
                        "Theoretischer Rahmen",
                        "Methodik",
                        "Ergebnisse & Analyse",
                        "Fazit & Ausblick",
                    ][:count]
                )
            ]
        )
        return version, list(version.nodes.order_by("order"))

    def _research_chapters(self, project, nodes):
        from apps.projects.services.citation_service import research_outline_node

        llm_key = getattr(settings, "TOGETHER_API_KEY", "")
        project_topic = project.description or project.title

        for node in nodes:
            self.stdout.write(f"  🔍 {node.order}. {node.title}...", ending="")
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
                self.stdout.write(self.style.SUCCESS(f" ✓ ({paper_count} Papers)"))
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f" ✗ ({exc})"))
                logger.warning("Research failed for node %s: %s", node.title, exc)

    def _write_chapters(self, project, user, nodes, max_iterations, llm_overrides=None):
        from apps.authoring.services.chapter_production_service import (
            ChapterProductionService,
        )

        svc = ChapterProductionService(
            project_id=str(project.pk),
            user=user,
            llm_overrides=llm_overrides,
        )
        total_words = 0

        for node in nodes:
            target = node.target_words or DEFAULT_TARGET_WORD_COUNT
            self.stdout.write(
                f"  ✍  {node.order}. {node.title} ({target} Wörter)...",
                ending="",
            )
            try:
                result = svc.produce_chapter(
                    chapter_id=str(node.pk),
                    target_words=target,
                    max_iterations=max_iterations,
                    auto_commit=False,
                )

                if result.success and result.write and result.write.content:
                    node.content = result.write.content
                    node.save(update_fields=["content", "word_count", "content_updated_at"])
                    wc = node.word_count
                    total_words += wc

                    score = ""
                    if result.analyze and result.analyze.overall_score:
                        score = f", Score: {result.analyze.overall_score}"
                    gate = ""
                    if result.gate:
                        gate = f", Gate: {result.gate.decision}"

                    self.stdout.write(self.style.SUCCESS(f" ✓ ({wc} Wörter, {result.iterations} Iter.{score}{gate})"))
                else:
                    error = result.error or "Unbekannter Fehler"
                    self.stdout.write(self.style.ERROR(f" ✗ ({error})"))

            except Exception as exc:
                self.stdout.write(self.style.ERROR(f" ✗ ({exc})"))
                logger.exception("Write failed for node %s", node.pk)

        self.stdout.write(self.style.SUCCESS(f"\n  Gesamt: {total_words:,} Wörter geschrieben"))

    def _run_peer_review(self, project, user):
        from apps.projects.services.peer_review_service import run_peer_review

        self.stdout.write("  🔬 Starte 4-Agenten Peer Review...")
        try:
            session_id = run_peer_review(project, user)
            if session_id:
                from apps.projects.models import PeerReviewSession

                session = PeerReviewSession.objects.get(pk=session_id)
                verdict = session.verdict or "—"
                findings = session.finding_count or 0
                self.stdout.write(self.style.SUCCESS(f"  ✓ Review abgeschlossen: {verdict} ({findings} Findings)"))
                if session.summary:
                    self.stdout.write(f"    {session.summary[:200]}")
            else:
                self.stdout.write(
                    self.style.WARNING("  ⚠ Peer Review konnte nicht gestartet werden (keine Kapitel mit Inhalt?)")
                )
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"  ✗ Peer Review fehlgeschlagen: {exc}"))
            logger.exception("Peer review failed for project %s", project.pk)

    def _print_summary(self, project, nodes, elapsed):
        from apps.projects.models import OutlineNode

        fresh_nodes = OutlineNode.objects.filter(
            outline_version__project=project,
            outline_version__is_active=True,
        ).order_by("order")

        total_words = sum(n.word_count for n in fresh_nodes)
        written = sum(1 for n in fresh_nodes if n.word_count > 0)
        total = fresh_nodes.count()

        base_url = getattr(settings, "SITE_URL", "https://writing.iil.pet")

        self.stdout.write(self.style.MIGRATE_HEADING(f"\n{'=' * 60}\n  ERGEBNIS\n{'=' * 60}"))
        self.stdout.write(f"  Projekt:     {project.title}")
        self.stdout.write(f"  Projekt-ID:  {project.pk}")
        self.stdout.write(f"  Kapitel:     {written}/{total} geschrieben")
        self.stdout.write(f"  Wörter:      {total_words:,}")
        self.stdout.write(f"  Dauer:       {elapsed:.0f}s ({elapsed / 60:.1f} min)")
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"  → Web-UI: {base_url}/projekte/{project.pk}/"))
        self.stdout.write("")
