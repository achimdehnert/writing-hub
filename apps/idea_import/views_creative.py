"""
Ideen-Studio — Kreativagent Views (ADR-083)

Phase-Workflow:
  1. Dashboard   — Übersicht aller Sessions + Schnellstart
  2. Session     — Ideen anzeigen, bewerten, verfeinern
  3. Brainstorm  — (POST) LLM generiert 3-5 Buchideen
  4. Refine      — (POST) LLM verfeinert eine Idee
  5. Premise     — (POST) LLM generiert vollständige Premise
  6. Create      — (POST) Buchprojekt aus Idee anlegen
"""
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from promptfw.parsing import extract_json, extract_json_list

from .models_creative import BookIdea, CreativeSession

logger = logging.getLogger(__name__)


class CreativeDashboardView(LoginRequiredMixin, View):
    template_name = "ideas/creative_dashboard.html"

    def get(self, request):
        sessions = CreativeSession.objects.filter(owner=request.user)
        active = sessions.exclude(phase="done").first()
        recent = sessions.order_by("-updated_at")[:5]
        try:
            from apps.authors.models import WritingStyle
            style_dnas = WritingStyle.objects.filter(
                author__owner=request.user, is_active=True
            ).select_related("author").order_by("author__name", "name")[:5]
        except Exception:
            style_dnas = []
        return render(request, self.template_name, {
            "active_session": active,
            "recent_sessions": recent,
            "style_dnas": style_dnas,
        })


class CreativeSessionStartView(LoginRequiredMixin, View):
    """POST — Neue Session starten."""

    def post(self, request):
        title = request.POST.get("title", "").strip()
        inspiration = request.POST.get("inspiration", "").strip()
        genre = request.POST.get("genre", "").strip()
        session_type = request.POST.get("session_type", "literary").strip()
        research_field = request.POST.get("research_field", "").strip()
        if not title:
            messages.warning(request, "Bitte einen Arbeitstitel eingeben.")
            return redirect("ideas:creative_dashboard")
        session = CreativeSession.objects.create(
            owner=request.user,
            title=title,
            inspiration=inspiration,
            genre=genre,
            session_type=session_type,
            research_field=research_field,
        )
        return redirect("ideas:creative_session", pk=session.pk)


class CreativeSessionView(LoginRequiredMixin, View):
    template_name = "ideas/creative_session.html"

    def get(self, request, pk):
        session = get_object_or_404(CreativeSession, pk=pk, owner=request.user)
        ideas = session.ideas.order_by("order")
        try:
            from apps.authors.models import WritingStyle
            style_dnas = WritingStyle.objects.filter(
                author__owner=request.user, is_active=True
            ).select_related("author").order_by("name")[:10]
        except Exception:
            style_dnas = []
        return render(request, self.template_name, {
            "session": session,
            "ideas": ideas,
            "style_dnas": style_dnas,
        })


class CreativeBrainstormView(LoginRequiredMixin, View):
    """POST — LLM generiert 3-5 Ideen für die Session (literarisch oder wissenschaftlich)."""

    def post(self, request, pk):
        session = get_object_or_404(CreativeSession, pk=pk, owner=request.user)
        count = int(request.POST.get("count", 5))
        style_hint = request.POST.get("style_hint", session.style_dna_hint or "").strip()
        if style_hint:
            session.style_dna_hint = style_hint
            session.save(update_fields=["style_dna_hint"])

        is_scientific = session.session_type == CreativeSession.SessionType.SCIENTIFIC
        try:
            if is_scientific:
                ideas = _brainstorm_topics(session, count)
            else:
                ideas = _brainstorm_ideas(session, count)
            for i, idea_data in enumerate(ideas):
                BookIdea.objects.create(
                    session=session,
                    title=idea_data.get("title", f"Idee {i+1}"),
                    logline=idea_data.get("logline", ""),
                    hook=idea_data.get("hook", ""),
                    genre=idea_data.get("genre", session.genre),
                    themes=idea_data.get("themes", []),
                    order=session.ideas.count() + i,
                )
            session.phase = CreativeSession.Phase.REFINING
            session.save(update_fields=["phase"])
            messages.success(request, f"{len(ideas)} Ideen generiert.")
        except Exception as exc:
            logger.exception("Brainstorm error session=%s: %s", pk, exc)
            messages.error(request, f"KI-Fehler: {exc}")

        return redirect("ideas:creative_session", pk=pk)


class CreativeRefineView(LoginRequiredMixin, View):
    """POST — LLM verfeinert eine einzelne Idee (literarisch oder wissenschaftlich)."""

    def post(self, request, pk, idea_pk):
        session = get_object_or_404(CreativeSession, pk=pk, owner=request.user)
        idea = get_object_or_404(BookIdea, pk=idea_pk, session=session)
        is_scientific = session.session_type == CreativeSession.SessionType.SCIENTIFIC
        try:
            if is_scientific:
                refined = _refine_topic(idea, session)
            else:
                refined = _refine_idea(idea, session)
            idea.refined_logline = refined.get("refined_logline", idea.logline)
            idea.hook = refined.get("hook", idea.hook)
            idea.themes = refined.get("themes", idea.themes)
            idea.is_refined = True
            idea.save()
            messages.success(request, f'\u201e{idea.title}\u201c verfeinert.')
        except Exception as exc:
            logger.exception("Refine error idea=%s: %s", idea_pk, exc)
            messages.error(request, f"Fehler: {exc}")
        return redirect("ideas:creative_session", pk=pk)


class CreativeRateView(LoginRequiredMixin, View):
    """POST — Bewertung einer Idee setzen (AJAX)."""

    def post(self, request, pk, idea_pk):
        session = get_object_or_404(CreativeSession, pk=pk, owner=request.user)
        idea = get_object_or_404(BookIdea, pk=idea_pk, session=session)
        try:
            rating = int(request.POST.get("rating", 0))
            idea.rating = max(0, min(4, rating))
            idea.save(update_fields=["rating"])
            return JsonResponse({"ok": True, "rating": idea.rating})
        except Exception as exc:
            return JsonResponse({"ok": False, "error": str(exc)})


class CreativePremiseView(LoginRequiredMixin, View):
    """POST — LLM generiert vollständige Premise / Exposé für eine gewählte Idee."""

    def post(self, request, pk, idea_pk):
        session = get_object_or_404(CreativeSession, pk=pk, owner=request.user)
        idea = get_object_or_404(BookIdea, pk=idea_pk, session=session)
        is_scientific = session.session_type == CreativeSession.SessionType.SCIENTIFIC
        try:
            if is_scientific:
                premise_text = _generate_expose(idea, session)
            else:
                premise_text = _generate_premise(idea, session)
            idea.premise = premise_text
            idea.save(update_fields=["premise"])
            session.selected_idea = idea
            session.premise = premise_text
            session.phase = CreativeSession.Phase.PREMISE
            session.save(update_fields=["selected_idea", "premise", "phase"])
            label = "Exposé" if is_scientific else "Premise"
            messages.success(request, f'{label} für \u201e{idea.title}\u201c generiert.')
        except Exception as exc:
            logger.exception("Premise error idea=%s: %s", idea_pk, exc)
            messages.error(request, f"Fehler: {exc}")
        return redirect("ideas:creative_session", pk=pk)


class CreativeCreateProjectView(LoginRequiredMixin, View):
    """POST — Buchprojekt aus gewählter Idee anlegen."""

    def post(self, request, pk):
        session = get_object_or_404(CreativeSession, pk=pk, owner=request.user)
        idea = session.selected_idea
        if not idea:
            idea_pk = request.POST.get("idea_pk")
            if idea_pk:
                idea = get_object_or_404(BookIdea, pk=idea_pk, session=session)
                session.selected_idea = idea
                session.save(update_fields=["selected_idea"])
            else:
                messages.warning(
                    request,
                    "Bitte zuerst eine Idee auswählen.",
                )
                return redirect("ideas:creative_session", pk=pk)

        from apps.projects.models import BookProject
        title = request.POST.get("title", idea.title).strip() or idea.title
        description = session.premise or idea.logline

        is_scientific = session.session_type == CreativeSession.SessionType.SCIENTIFIC
        content_type_slug = None
        if is_scientific:
            content_type_slug = idea.genre if idea.genre in ("scientific", "academic") else "scientific"
        project = BookProject.objects.create(
            owner=request.user,
            title=title,
            description=description,
            genre=idea.genre,
        )
        if content_type_slug:
            try:
                from apps.projects.models import ContentTypeLookup
                ct = ContentTypeLookup.objects.filter(slug=content_type_slug).first()
                if ct:
                    project.content_type_lookup = ct
                    project.save(update_fields=["content_type_lookup"])
            except Exception:
                pass
        session.created_project = project
        session.phase = CreativeSession.Phase.DONE
        session.save(update_fields=["created_project", "phase"])
        messages.success(request, f'Projekt \u201e{project.title}\u201c angelegt.')
        return redirect("projects:detail", pk=project.pk)


class CreativeSessionDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        session = get_object_or_404(CreativeSession, pk=pk, owner=request.user)
        session.delete()
        messages.info(request, "Session gelöscht.")
        return redirect("ideas:creative_dashboard")


# ---------------------------------------------------------------------------
# LLM helpers
# ---------------------------------------------------------------------------

def _get_router():
    from apps.authoring.services.llm_router import LLMRouter
    return LLMRouter()


def _style_block(session: CreativeSession) -> str:
    if session.style_dna_hint:
        return f"Schreibstil-Hinweis: {session.style_dna_hint}"
    return ""


def _brainstorm_ideas(session: CreativeSession, count: int = 5) -> list[dict]:
    from apps.core.prompt_utils import render_prompt

    router = _get_router()
    messages = render_prompt(
        "idea_import/brainstorm_ideas",
        inspiration=session.inspiration or "",
        genre=session.genre or "",
        style_hint=session.style_dna_hint or "",
        count=count,
    )
    if not messages:
        # Fallback if template not found
        messages = [
            {"role": "system", "content": "Du bist ein kreativer Buchentwickler. Antworte NUR mit JSON."},
            {"role": "user", "content": f"Generiere {count} Buchideen als JSON-Array."},
        ]
    raw = router.completion(action_code="outline_generate", messages=messages)
    data = extract_json_list(raw)
    if data:
        return data
    obj = extract_json(raw)
    return obj.get("ideas", []) if obj else []


def _refine_idea(idea: BookIdea, session: CreativeSession) -> dict:
    from apps.core.prompt_utils import render_prompt

    router = _get_router()
    messages = render_prompt(
        "idea_import/refine_idea",
        title=idea.title,
        logline=idea.logline,
        hook=idea.hook,
        style_hint=session.style_dna_hint or "",
    )
    if not messages:
        messages = [
            {"role": "system", "content": "Du bist ein Lektor. Antworte NUR mit JSON."},
            {"role": "user", "content": f"Verfeinere: {idea.title}"},
        ]
    raw = router.completion(action_code="outline_generate", messages=messages)
    return extract_json(raw) or {}


def _brainstorm_topics(session: CreativeSession, count: int = 5) -> list[dict]:
    """Generiert wissenschaftliche Themenvorschläge als JSON-Array."""
    from apps.core.prompt_utils import render_prompt

    router = _get_router()
    messages = render_prompt(
        "idea_import/brainstorm_topics",
        research_field=session.research_field or "",
        inspiration=session.inspiration or "",
        count=count,
    )
    if not messages:
        messages = [
            {"role": "system", "content": "Du bist ein Wissenschaftsberater. Antworte NUR mit JSON."},
            {"role": "user", "content": f"Generiere {count} Themenvorschläge als JSON-Array."},
        ]
    raw = router.completion(action_code="outline_generate", messages=messages)
    data = extract_json_list(raw)
    if data:
        return data
    obj = extract_json(raw)
    return obj.get("ideas", obj.get("topics", [])) if obj else []


def _refine_topic(idea: BookIdea, session: CreativeSession) -> dict:
    """Schärft ein wissenschaftliches Thema: Forschungsfrage, Methodik, Beitrag."""
    from apps.core.prompt_utils import render_prompt

    router = _get_router()
    messages = render_prompt(
        "idea_import/refine_topic",
        title=idea.title,
        logline=idea.logline,
        hook=idea.hook,
        research_field=session.research_field or "",
    )
    if not messages:
        messages = [
            {"role": "system", "content": "Du bist ein Wissenschaftsberater. Antworte NUR mit JSON."},
            {"role": "user", "content": f"Verfeinere: {idea.title}"},
        ]
    raw = router.completion(action_code="outline_generate", messages=messages)
    return extract_json(raw) or {}


def _generate_expose(idea: BookIdea, session: CreativeSession) -> str:
    """Generiert ein wissenschaftliches Exposé (Forschungsfrage, Stand, Methodik, Relevanz)."""
    from apps.core.prompt_utils import render_prompt

    router = _get_router()
    logline = idea.refined_logline or idea.logline
    messages = render_prompt(
        "idea_import/generate_expose",
        title=idea.title,
        logline=logline,
        hook=idea.hook,
        themes=idea.themes or [],
        research_field=session.research_field or "",
    )
    if not messages:
        messages = [
            {"role": "system", "content": "Du bist ein Wissenschaftsberater."},
            {"role": "user", "content": f"Erstelle ein Exposé für: {idea.title}"},
        ]
    return router.completion(action_code="outline_generate", messages=messages)


def _generate_premise(idea: BookIdea, session: CreativeSession) -> str:
    from apps.core.prompt_utils import render_prompt

    router = _get_router()
    logline = idea.refined_logline or idea.logline
    messages = render_prompt(
        "idea_import/generate_premise",
        title=idea.title,
        logline=logline,
        genre=idea.genre or "",
        themes=idea.themes or [],
        style_hint=session.style_dna_hint or "",
    )
    if not messages:
        messages = [
            {"role": "system", "content": "Du bist ein Buchentwickler."},
            {"role": "user", "content": f"Erstelle eine Premise für: {idea.title}"},
        ]
    return router.completion(action_code="outline_generate", messages=messages)
