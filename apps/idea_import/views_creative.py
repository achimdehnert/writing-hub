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
import json
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

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
        if not title:
            messages.warning(request, "Bitte einen Arbeitstitel eingeben.")
            return redirect("ideas:creative_dashboard")
        session = CreativeSession.objects.create(
            owner=request.user,
            title=title,
            inspiration=inspiration,
            genre=genre,
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
    """POST — LLM generiert 3-5 Buchideen für die Session."""

    def post(self, request, pk):
        session = get_object_or_404(CreativeSession, pk=pk, owner=request.user)
        count = int(request.POST.get("count", 5))
        style_hint = request.POST.get("style_hint", session.style_dna_hint or "").strip()
        if style_hint:
            session.style_dna_hint = style_hint
            session.save(update_fields=["style_dna_hint"])

        try:
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
    """POST — LLM verfeinert eine einzelne Buchidee."""

    def post(self, request, pk, idea_pk):
        session = get_object_or_404(CreativeSession, pk=pk, owner=request.user)
        idea = get_object_or_404(BookIdea, pk=idea_pk, session=session)
        try:
            refined = _refine_idea(idea, session)
            idea.refined_logline = refined.get("refined_logline", idea.logline)
            idea.hook = refined.get("hook", idea.hook)
            idea.themes = refined.get("themes", idea.themes)
            idea.is_refined = True
            idea.save()
            messages.success(request, f'„{idea.title}\u201c verfeinert.')
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
    """POST — LLM generiert vollständige Premise für eine gewählte Idee."""

    def post(self, request, pk, idea_pk):
        session = get_object_or_404(CreativeSession, pk=pk, owner=request.user)
        idea = get_object_or_404(BookIdea, pk=idea_pk, session=session)
        try:
            premise_text = _generate_premise(idea, session)
            idea.premise = premise_text
            idea.save(update_fields=["premise"])
            session.selected_idea = idea
            session.premise = premise_text
            session.phase = CreativeSession.Phase.PREMISE
            session.save(update_fields=["selected_idea", "premise", "phase"])
            messages.success(request, f'Premise für \u201e{idea.title}\u201c generiert.')
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
            messages.warning(request, "Bitte zuerst eine Idee auswählen und eine Premise generieren.")
            return redirect("ideas:creative_session", pk=pk)

        from apps.projects.models import BookProject
        title = request.POST.get("title", idea.title).strip() or idea.title
        description = session.premise or idea.logline

        project = BookProject.objects.create(
            owner=request.user,
            title=title,
            description=description,
            genre=idea.genre,
        )
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
    router = _get_router()
    style = _style_block(session)
    genre_hint = f"Genre: {session.genre}" if session.genre else ""
    inspiration = f"Inspiration: {session.inspiration}" if session.inspiration else ""

    system = (
        "Du bist ein kreativer Buchentwickler. Generiere originelle, packende Buchideen.\n"
        "Antworte NUR mit gültigem JSON, kein Markdown."
    )
    user = (
        f"{inspiration}\n{genre_hint}\n{style}\n\n"
        f"Generiere {count} verschiedene Buchideen als JSON-Array:\n"
        '[{"title": "...", "logline": "1-2 Sätze: Wer will was und warum scheitert er?", '
        '"hook": "Was macht diese Idee besonders?", "genre": "...", "themes": ["..."]}, ...]\n'
        "Jede Idee soll einzigartig und spannend sein. Nur JSON."
    )
    raw = router.completion(action_code="outline_gen", messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ])
    clean = raw.strip().lstrip("`").removeprefix("json").strip().rstrip("`")
    data = json.loads(clean)
    return data if isinstance(data, list) else data.get("ideas", [])


def _refine_idea(idea: BookIdea, session: CreativeSession) -> dict:
    router = _get_router()
    style = _style_block(session)
    system = (
        "Du bist ein erfahrener Lektor und Buchentwickler.\n"
        "Verfeinere Buchideen: schärfe die Logline, verbessere den Hook, "
        "identifiziere tiefere Themen.\n"
        "Antworte NUR mit gültigem JSON."
    )
    user = (
        f"Idee: {idea.title}\n"
        f"Logline: {idea.logline}\n"
        f"Hook: {idea.hook}\n"
        f"{style}\n\n"
        'JSON: {"refined_logline": "...", "hook": "...", "themes": ["..."]}'
    )
    raw = router.completion(action_code="outline_gen", messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ])
    clean = raw.strip().lstrip("`").removeprefix("json").strip().rstrip("`")
    return json.loads(clean)


def _generate_premise(idea: BookIdea, session: CreativeSession) -> str:
    router = _get_router()
    style = _style_block(session)
    system = (
        "Du bist ein erfahrener Buchentwickler. Erstelle eine vollständige Buchpremise.\n"
        "Antworte nur mit dem Premise-Text, kein JSON, keine Erklärungen."
    )
    logline = idea.refined_logline or idea.logline
    user = (
        f"Titel: {idea.title}\n"
        f"Logline: {logline}\n"
        f"Genre: {idea.genre}\n"
        f"Themen: {', '.join(idea.themes or [])}\n"
        f"{style}\n\n"
        "Erstelle eine vollständige Buchpremise (250-400 Wörter): Protagonist, Welt, Konflikt, "
        "Wendepunkte, emotionaler Kern, thematische Aussage."
    )
    return router.completion(action_code="outline_gen", messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ])
