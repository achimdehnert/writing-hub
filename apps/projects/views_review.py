"""
Review & Redaktion — HTML Views (ADR-083)
"""
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView
from promptfw.parsing import extract_json_list

from .models import BookProject, OutlineNode, OutlineVersion

logger = logging.getLogger(__name__)

AI_REVIEW_AGENTS = [
    {"key": "style_critic", "name": "Stil-Kritiker", "icon": "bi-brush",
     "description": "Analysiert Schreibstil, Sprache und Ausdrucksweise"},
    {"key": "story_editor", "name": "Story-Editor", "icon": "bi-diagram-3",
     "description": "Prüft Handlung, Charakterkonsistenz und Pacing"},
    {"key": "lector", "name": "Lektor", "icon": "bi-check2-square",
     "description": "Findet Fehler, Widersprüche und Schwachstellen"},
    {"key": "beta_reader", "name": "Beta-Leser", "icon": "bi-person-raised-hand",
     "description": "Gibt Leserperspektive und emotionale Reaktion"},
    {"key": "genre_expert", "name": "Genre-Experte", "icon": "bi-award",
     "description": "Bewertet Genre-Konventionen und Erwartungen"},
]


def _get_project(user, pk):
    return get_object_or_404(BookProject, pk=pk, owner=user)


def _get_chapters(project):
    version = OutlineVersion.objects.filter(
        project=project, is_active=True
    ).order_by("-created_at").first()
    if not version:
        return []
    return list(version.nodes.order_by("order"))


class ProjectReviewView(LoginRequiredMixin, DetailView):
    model = BookProject
    template_name = "projects/review.html"
    context_object_name = "project"

    def get_queryset(self):
        return BookProject.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from .models import ChapterReview
        project = self.object
        chapters = _get_chapters(project)
        reviews = ChapterReview.objects.filter(
            node__outline_version__project=project
        ).select_related("node")
        open_reviews = reviews.filter(is_resolved=False).count()
        done_reviews = reviews.filter(is_resolved=True).count()
        review_map = {}
        for r in reviews:
            review_map.setdefault(str(r.node_id), []).append(r)
        ctx["chapters"] = chapters
        ctx["chapter_count"] = len(chapters)
        ctx["open_reviews"] = open_reviews
        ctx["done_reviews"] = done_reviews
        ctx["review_map"] = review_map
        ctx["ai_agents"] = AI_REVIEW_AGENTS
        return ctx


class ProjectReviewChapterView(LoginRequiredMixin, DetailView):
    model = BookProject
    template_name = "projects/review_chapter.html"
    context_object_name = "project"

    def get_queryset(self):
        return BookProject.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from .models import ChapterReview
        node_pk = self.kwargs["node_pk"]
        node = get_object_or_404(
            OutlineNode, pk=node_pk,
            outline_version__project=self.object
        )
        reviews = ChapterReview.objects.filter(node=node).order_by("-created_at")
        ctx["node"] = node
        ctx["reviews"] = reviews
        ctx["open_count"] = reviews.filter(is_resolved=False).count()
        ctx["ai_agents"] = AI_REVIEW_AGENTS
        return ctx


class ChapterReviewAddView(LoginRequiredMixin, View):
    def post(self, request, pk, node_pk):
        from .models import ChapterReview
        node = get_object_or_404(
            OutlineNode, pk=node_pk,
            outline_version__project__owner=request.user
        )
        feedback = request.POST.get("feedback", "").strip()
        if not feedback:
            messages.warning(request, "Bitte Feedback eingeben.")
            return redirect("projects:review_chapter", pk=pk, node_pk=node_pk)
        ChapterReview.objects.create(
            node=node,
            created_by=request.user,
            reviewer=request.POST.get("reviewer", "Autor"),
            feedback_type=request.POST.get("feedback_type", "suggestion"),
            feedback=feedback,
            text_reference=request.POST.get("text_reference", ""),
        )
        messages.success(request, "Feedback hinzugefügt.")
        return redirect("projects:review_chapter", pk=pk, node_pk=node_pk)


class ChapterReviewResolveView(LoginRequiredMixin, View):
    def post(self, request, pk, review_pk):
        from .models import ChapterReview
        review = get_object_or_404(
            ChapterReview, pk=review_pk,
            node__outline_version__project__owner=request.user
        )
        review.is_resolved = not review.is_resolved
        review.save(update_fields=["is_resolved"])
        return JsonResponse({"ok": True, "is_resolved": review.is_resolved})


class ChapterAIReviewView(LoginRequiredMixin, View):
    """KI-Review für ein Kapitel mit ausgewähltem Agent."""

    def post(self, request, pk, node_pk):
        from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError
        from .models import ChapterReview

        node = get_object_or_404(
            OutlineNode, pk=node_pk,
            outline_version__project__owner=request.user
        )
        agent_key = request.POST.get("agent", "lector")
        agent = next((a for a in AI_REVIEW_AGENTS if a["key"] == agent_key), AI_REVIEW_AGENTS[2])

        if not node.content or not node.content.strip():
            messages.warning(request, "Kapitel hat noch keinen Inhalt zum Reviewen.")
            return redirect("projects:review_chapter", pk=pk, node_pk=node_pk)

        from apps.core.prompt_utils import render_prompt
        template_map = {
            "story_editor": "projects/review_story_editor",
            "lector": "projects/review_lector",
            "beta_reader": "projects/review_beta_reader",
            "genre_expert": "projects/review_genre_expert",
            "dramaturg": "projects/review_dramaturg",
        }
        template_name = template_map.get(agent_key, "projects/review_lector")
        prompt_msgs = render_prompt(
            template_name,
            order=node.order,
            title=node.title,
            content=node.content,
        )

        try:
            router = LLMRouter()
            raw = router.completion(
                action_code="chapter_analyze",
                messages=prompt_msgs,
            )
            items = extract_json_list(raw)
            if items:
                created = 0
                for item in items[:10]:
                    fb = item.get("feedback", "").strip()
                    if not fb:
                        continue
                    ftype = item.get("type", "suggestion")
                    if ftype not in ("positive", "suggestion", "issue", "question"):
                        ftype = "suggestion"
                    ChapterReview.objects.create(
                        node=node,
                        created_by=request.user,
                        reviewer=agent["name"],
                        feedback_type=ftype,
                        feedback=fb,
                        text_reference=item.get("text_ref", ""),
                        is_ai_generated=True,
                        ai_agent=agent_key,
                    )
                    created += 1
                messages.success(request, f"{agent['name']}: {created} Feedback-Einträge erstellt.")
            else:
                ChapterReview.objects.create(
                    node=node,
                    created_by=request.user,
                    reviewer=agent["name"],
                    feedback_type="suggestion",
                    feedback=raw[:2000],
                    is_ai_generated=True,
                    ai_agent=agent_key,
                )
                messages.success(request, f"{agent['name']}: Review erstellt.")
        except LLMRoutingError as exc:
            messages.warning(request, f"KI nicht verfügbar: {exc}")
        except Exception as exc:
            logger.exception("ChapterAIReview error: %s", exc)
            messages.error(request, f"Fehler: {exc}")

        return redirect("projects:review_chapter", pk=pk, node_pk=node_pk)


class ProjectEditingView(LoginRequiredMixin, DetailView):
    model = BookProject
    template_name = "projects/editing.html"
    context_object_name = "project"

    def get_queryset(self):
        return BookProject.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from .models import ChapterEditing
        project = self.object
        chapters = _get_chapters(project)
        editings = ChapterEditing.objects.filter(
            node__outline_version__project=project
        ).select_related("node")
        open_suggestions = editings.filter(is_accepted__isnull=True).count()
        editing_map = {}
        for e in editings:
            editing_map.setdefault(str(e.node_id), []).append(e)
        ctx["chapters"] = chapters
        ctx["chapter_count"] = len(chapters)
        ctx["open_suggestions"] = open_suggestions
        ctx["open_feedback"] = 0
        ctx["editing_map"] = editing_map
        return ctx


class ChapterEditingView(LoginRequiredMixin, DetailView):
    model = BookProject
    template_name = "projects/editing_chapter.html"
    context_object_name = "project"

    def get_queryset(self):
        return BookProject.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from .models import ChapterEditing
        node_pk = self.kwargs["node_pk"]
        node = get_object_or_404(
            OutlineNode, pk=node_pk,
            outline_version__project=self.object
        )
        editings = ChapterEditing.objects.filter(node=node).order_by("-created_at")
        ctx["node"] = node
        ctx["editings"] = editings
        ctx["open_count"] = editings.filter(is_accepted__isnull=True).count()
        return ctx


class ChapterAIEditingView(LoginRequiredMixin, View):
    """KI-Editing: Analysiert ein Kapitel und erstellt Verbesserungsvorschläge."""

    def post(self, request, pk, node_pk):
        from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError
        from .models import ChapterEditing

        node = get_object_or_404(
            OutlineNode, pk=node_pk,
            outline_version__project__owner=request.user
        )
        if not node.content or not node.content.strip():
            messages.warning(request, "Kapitel hat noch keinen Inhalt zum Analysieren.")
            return redirect("projects:editing_chapter", pk=pk, node_pk=node_pk)

        system_prompt = (
            "Du bist ein professioneller Lektor und Stilberater.\n"
            "Erstelle konkrete Verbesserungsvorschläge für den Text.\n"
            "Für jeden Vorschlag: Original-Textstelle, Verbesserung, Erklärung, Typ.\n"
            "Antworte als JSON-Array:\n"
            "[{\"type\": \"style|clarity|consistency|grammar|pacing|character\",\n"
            " \"original\": \"Originaltext...\",\n"
            " \"suggestion\": \"Verbesserter Text...\",\n"
            " \"explanation\": \"Warum diese Änderung...\"}]"
        )
        user_prompt = (
            f"Kapitel {node.order}: {node.title}\n\n"
            f"{node.content[:8000]}"
        )

        try:
            router = LLMRouter()
            raw = router.completion(
                action_code="chapter_analyze",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            items = extract_json_list(raw)
            if items:
                created = 0
                for item in items[:15]:
                    sug = item.get("suggestion", "").strip()
                    if not sug:
                        continue
                    stype = item.get("type", "style")
                    if stype not in ("style", "clarity", "consistency", "grammar", "pacing", "character"):
                        stype = "style"
                    ChapterEditing.objects.create(
                        node=node,
                        created_by=request.user,
                        suggestion_type=stype,
                        original_text=item.get("original", ""),
                        suggestion=sug,
                        explanation=item.get("explanation", ""),
                        is_ai_generated=True,
                    )
                    created += 1
                messages.success(request, f"{created} Verbesserungsvorschläge erstellt.")
            else:
                ChapterEditing.objects.create(
                    node=node,
                    created_by=request.user,
                    suggestion_type="style",
                    suggestion=raw[:2000],
                    is_ai_generated=True,
                )
                messages.success(request, "Analyse abgeschlossen.")
        except LLMRoutingError as exc:
            messages.warning(request, f"KI nicht verfügbar: {exc}")
        except Exception as exc:
            logger.exception("ChapterAIEditing error: %s", exc)
            messages.error(request, f"Fehler: {exc}")

        return redirect("projects:editing_chapter", pk=pk, node_pk=node_pk)


class ChapterEditingSuggestionView(LoginRequiredMixin, View):
    """Vorschlag annehmen oder ablehnen."""

    def post(self, request, pk, editing_pk):
        from .models import ChapterEditing
        editing = get_object_or_404(
            ChapterEditing, pk=editing_pk,
            node__outline_version__project__owner=request.user
        )
        action = request.POST.get("action")
        if action == "accept":
            editing.is_accepted = True
            editing.save(update_fields=["is_accepted"])
            return JsonResponse({"ok": True, "accepted": True})
        elif action == "reject":
            editing.is_accepted = False
            editing.save(update_fields=["is_accepted"])
            return JsonResponse({"ok": True, "accepted": False})
        return JsonResponse({"ok": False})
