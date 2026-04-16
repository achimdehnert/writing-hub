"""
Idea Import — HTML Frontend Views
"""
import logging
import uuid

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView

from apps.authoring.defaults import (
    DEFAULT_CONTENT_TYPE,
    DEFAULT_PROJECT_TARGET_WORDS,
    distribute_chapter_targets,
)
from apps.projects.models import BookProject
from .models import IdeaImportDraft

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


class IdeaListView(LoginRequiredMixin, ListView):
    model = IdeaImportDraft
    template_name = "ideas/idea_list.html"
    context_object_name = "drafts"
    paginate_by = 20

    def get_queryset(self):
        return (
            IdeaImportDraft.objects
            .filter(project__owner=self.request.user)
            .exclude(status=IdeaImportDraft.Status.DISCARDED)
            .select_related("project")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        ctx["total"] = qs.count()
        ctx["pending"] = qs.filter(status=IdeaImportDraft.Status.PENDING_REVIEW).count()
        ctx["committed"] = qs.filter(status=IdeaImportDraft.Status.COMMITTED).count()
        ctx["projects"] = BookProject.objects.filter(owner=self.request.user, is_active=True).order_by("title")
        return ctx


class IdeaUploadView(LoginRequiredMixin, View):
    """Datei-Upload oder Freitext → KI-Extraktion → IdeaImportDraft."""

    def get(self, request):
        projects = BookProject.objects.filter(owner=request.user, is_active=True).order_by("title")
        return render(request, "ideas/idea_upload.html", {"projects": projects})

    def post(self, request):
        from apps.idea_import.services.document_normalizer import (
            DocumentNormalizerService, UnsupportedFormatError,
        )
        from apps.idea_import.services.idea_extractor import (
            extract_ideas, available_sections,
        )

        project_id = request.POST.get("project_id")
        if not project_id:
            messages.error(request, "Bitte ein Projekt auswählen.")
            return redirect("ideas:upload")

        project = get_object_or_404(BookProject, pk=project_id, owner=request.user)
        input_type = request.POST.get("input_type", "file")

        try:
            if input_type == "freetext":
                text = request.POST.get("freetext_content", "").strip()
                if len(text) < 20:
                    messages.error(request, "Freitext zu kurz (mindestens 20 Zeichen).")
                    return redirect("ideas:upload")
                normalized_text, source_format = DocumentNormalizerService.normalize_freetext(text)
                source_filename = ""
            else:
                uploaded_file = request.FILES.get("document_file")
                if not uploaded_file:
                    messages.error(request, "Keine Datei hochgeladen.")
                    return redirect("ideas:upload")
                if uploaded_file.size > MAX_UPLOAD_BYTES:
                    messages.error(request, "Datei zu groß (max. 10 MB).")
                    return redirect("ideas:upload")
                source_filename = uploaded_file.name
                file_content = uploaded_file.read()
                normalized_text, source_format = DocumentNormalizerService.normalize_upload(
                    file_content=file_content,
                    filename=source_filename,
                )

            if len(normalized_text.strip()) < 20:
                messages.error(request, "Dokument ist leer oder konnte nicht ausgelesen werden.")
                return redirect("ideas:upload")

            extracted_data = extract_ideas(normalized_text)

            draft = IdeaImportDraft.objects.create(
                project=project,
                created_by=request.user,
                source_filename=source_filename,
                source_format=source_format,
                source_text=normalized_text[:20_000],
                extracted_data=extracted_data,
                extraction_model="aifw/idea_extraction",
                status=IdeaImportDraft.Status.PENDING_REVIEW,
            )

            sections = available_sections(extracted_data)
            logger.info("IdeaUpload: project=%s draft=%s sections=%s", project.pk, draft.pk, sections)
            messages.success(request, f"Extraktion: {', '.join(sections) or 'keine Sektionen erkannt'}.")
            return redirect("ideas:review", pk=draft.pk)

        except UnsupportedFormatError as exc:
            messages.error(request, str(exc))
            return redirect("ideas:upload")
        except Exception as exc:
            logger.exception("IdeaUpload Fehler: %s", exc)
            messages.error(request, f"Fehler: {exc}")
            return redirect("ideas:upload")


class IdeaReviewView(LoginRequiredMixin, View):
    """Extraktionsergebnis reviewen + Sektionen auswählen."""

    def get(self, request, pk):
        from apps.idea_import.services.idea_extractor import available_sections, section_summary
        draft = get_object_or_404(IdeaImportDraft, pk=pk, project__owner=request.user)
        data = draft.extracted_data or {}
        return render(request, "ideas/idea_review.html", {
            "draft": draft,
            "data": data,
            "sections": available_sections(data),
            "summary": section_summary(data),
            "confidence": data.get("confidence_scores", {}),
        })

    def post(self, request, pk):
        draft = get_object_or_404(IdeaImportDraft, pk=pk, project__owner=request.user)
        action = request.POST.get("action", "commit")

        if action == "discard":
            draft.status = IdeaImportDraft.Status.DISCARDED
            draft.save(update_fields=["status"])
            messages.info(request, "Ideen-Import verworfen.")
            return redirect("ideas:list")

        approved = request.POST.getlist("sections")
        if not approved:
            messages.warning(request, "Keine Sektionen ausgewählt.")
            return redirect("ideas:review", pk=pk)

        data = draft.extracted_data or {}
        project = draft.project
        stats = {}

        try:
            from django.db import transaction
            with transaction.atomic():
                if "metadata" in approved:
                    stats["metadata"] = _commit_metadata(project, data)
                if "outline" in approved:
                    stats["outline"] = _commit_outline(project, data, request.user)
                if "characters" in approved:
                    stats["characters"] = _commit_characters(project, data)
                if "world" in approved:
                    stats["world"] = _commit_world(project, data)

            committed_all = set(approved) >= set(_available_sections_from_data(data))
            draft.status = (
                IdeaImportDraft.Status.COMMITTED if committed_all
                else IdeaImportDraft.Status.PARTIAL
            )
            draft.committed_sections = approved
            draft.save(update_fields=["status", "committed_sections"])

            parts = []
            if "metadata" in stats:
                parts.append(f"{stats['metadata']} Metadaten")
            if "outline" in stats:
                parts.append(f"{stats['outline']} Outline-Beats")
            if "characters" in stats:
                parts.append(f"{stats['characters']} Charaktere")
            if "world" in stats:
                parts.append(f"{stats['world']} Welt-Elemente")
            messages.success(request, f"Commit: {', '.join(parts)}." if parts else "Commit abgeschlossen.")
            return redirect("projects:detail", pk=project.pk)

        except Exception as exc:
            logger.exception("IdeaReview Commit-Fehler: %s", exc)
            messages.error(request, f"Fehler beim Commit: {exc}")
            return redirect("ideas:review", pk=pk)


def _available_sections_from_data(data: dict) -> list[str]:
    from apps.idea_import.services.idea_extractor import available_sections
    return available_sections(data)


def _commit_metadata(project, data: dict) -> int:
    updated = 0
    fields = []
    if data.get("title") and not project.title:
        project.title = data["title"]
        fields.append("title")
        updated += 1
    if data.get("description") and not project.description:
        project.description = data["description"]
        fields.append("description")
        updated += 1
    if fields:
        project.save(update_fields=fields)
    return updated


def _commit_outline(project, data: dict, user) -> int:
    from apps.projects.models import OutlineVersion, OutlineNode
    from django.utils import timezone

    beats = data.get("outline_beats", [])
    chapters = data.get("chapters", [])

    all_beats = []
    for i, b in enumerate(beats):
        all_beats.append({
            "title": b.get("title", f"Beat {i+1}"),
            "description": b.get("description", ""),
            "beat_type": b.get("beat_type", "chapter"),
            "order": b.get("order", i + 1),
        })
    for i, ch in enumerate(chapters):
        all_beats.append({
            "title": ch.get("title", f"Kapitel {ch.get('number', i+1)}"),
            "description": ch.get("summary", ""),
            "beat_type": "chapter",
            "order": ch.get("number", len(beats) + i + 1),
        })

    if not all_beats:
        return 0

    version = OutlineVersion.objects.create(
        project=project,
        created_by=user,
        name=f"Import {timezone.now().strftime('%d.%m.%Y %H:%M')}",
        source="idea_import",
        is_active=True,
    )
    ct = getattr(project, "content_type", DEFAULT_CONTENT_TYPE) or DEFAULT_CONTENT_TYPE
    ptarget = project.target_word_count or DEFAULT_PROJECT_TARGET_WORDS
    targets = distribute_chapter_targets(ptarget, len(all_beats), ct)
    OutlineNode.objects.bulk_create([
        OutlineNode(
            outline_version=version,
            title=b["title"],
            description=b["description"],
            beat_type=b["beat_type"],
            order=b["order"],
            target_words=targets[i],
        )
        for i, b in enumerate(all_beats)
    ])
    return len(all_beats)


def _commit_characters(project, data: dict) -> int:
    """
    Charaktere als ProjectCharacterLink anlegen.
    Da writing-hub SSoT WeltenHub ist, werden hier nur Platzhalter-UUIDs
    erstellt — echte WeltenHub-Integration erfordert API-Aufruf.
    Vorerst: Charakter-Namen werden als notes gespeichert.
    """
    from apps.worlds.models import ProjectCharacterLink

    characters = data.get("characters", [])
    count = 0
    for char in characters:
        name = char.get("name", "").strip()
        if not name:
            continue
        role = char.get("role", "supporting")
        description = char.get("description", "")
        arc = char.get("arc", "")
        placeholder_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"{project.pk}:{name}")
        _, created = ProjectCharacterLink.objects.get_or_create(
            project=project,
            weltenhub_character_id=placeholder_id,
            defaults={
                "project_role": role,
                "project_arc": arc,
                "notes": f"{name}: {description[:200]}" if description else name,
            },
        )
        if created:
            count += 1
    return count


def _commit_world(project, data: dict) -> int:
    """
    Welt-Elemente als ProjectWorldLink-Notes anlegen.
    Vorerst: Ein Link mit allen Welt-Elementen als notes.
    """
    from apps.worlds.models import ProjectWorldLink

    world_elements = data.get("world_elements", [])
    if not world_elements:
        return 0

    notes_parts = []
    for elem in world_elements:
        name = elem.get("name", "").strip()
        desc = elem.get("description", "").strip()
        etype = elem.get("element_type", "concept")
        if name:
            notes_parts.append(f"[{etype}] {name}: {desc[:100]}" if desc else f"[{etype}] {name}")

    if not notes_parts:
        return 0

    placeholder_world_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"{project.pk}:idea_import")
    _, created = ProjectWorldLink.objects.get_or_create(
        project=project,
        weltenhub_world_id=placeholder_world_id,
        defaults={
            "role": "primary",
            "notes": "\n".join(notes_parts)[:2000],
        },
    )
    return len(world_elements) if created else 0
