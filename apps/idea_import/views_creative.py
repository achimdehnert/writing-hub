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
            messages.warning(request, "Bitte zuerst eine Idee auswählen und eine Premise generieren.")
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
    raw = router.completion(action_code="outline_generate", messages=[
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
    raw = router.completion(action_code="outline_generate", messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ])
    clean = raw.strip().lstrip("`").removeprefix("json").strip().rstrip("`")
    return json.loads(clean)


def _brainstorm_topics(session: CreativeSession, count: int = 5) -> list[dict]:
    """Generiert wissenschaftliche Themenvorschläge als JSON-Array."""
    router = _get_router()
    field_hint = f"Fachgebiet: {session.research_field}" if session.research_field else ""
    inspiration = f"Themenrichtung: {session.inspiration}" if session.inspiration else ""
    system = (
        "Du bist ein erfahrener Wissenschaftsberater. "
        "Generiere originelle, forschungsrelevante Themenvorschläge.\n"
        "Antworte NUR mit gültigem JSON, kein Markdown."
    )
    user = (
        f"{field_hint}\n{inspiration}\n\n"
        f"Generiere {count} verschiedene wissenschaftliche Themenvorschläge als JSON-Array:\n"
        '[{"title": "Thementitel", '
        '"logline": "Kernfrage und Relevanz in 1-2 Sätzen", '
        '"hook": "Was ist der innovative Beitrag?", '
        '"genre": "scientific", '
        '"themes": ["Schlüsselkonzept1", "Schlüsselkonzept2"]}, ...]\n'
        "Jedes Thema soll eine klare Forschungsfrage und wissenschaftlichen Mehrwert haben. Nur JSON."
    )
    raw = router.completion(action_code="outline_generate", messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ])
    clean = raw.strip().lstrip("`").removeprefix("json").strip().rstrip("`")
    data = json.loads(clean)
    return data if isinstance(data, list) else data.get("ideas", data.get("topics", []))


def _refine_topic(idea: BookIdea, session: CreativeSession) -> dict:
    """Schärft ein wissenschaftliches Thema: Forschungsfrage, Methodik, Beitrag."""
    router = _get_router()
    field_hint = f"Fachgebiet: {session.research_field}" if session.research_field else ""
    system = (
        "Du bist ein erfahrener Wissenschaftsberater und Gutachter.\n"
        "Verfeinere wissenschaftliche Themenvorschläge: schärfe die Forschungsfrage, "
        "identifiziere Methodik und wissenschaftlichen Beitrag.\n"
        "Antworte NUR mit gültigem JSON."
    )
    user = (
        f"Thema: {idea.title}\n"
        f"Kernfrage: {idea.logline}\n"
        f"Innovationsbeitrag: {idea.hook}\n"
        f"{field_hint}\n\n"
        'JSON: {"refined_logline": "Präzisierte Forschungsfrage", '
        '"hook": "Wissenschaftlicher Beitrag und Alleinstellungsmerkmal", '
        '"themes": ["Schlüsselbegriff1", "Schlüsselbegriff2"]}'
    )
    raw = router.completion(action_code="outline_generate", messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ])
    clean = raw.strip().lstrip("`").removeprefix("json").strip().rstrip("`")
    return json.loads(clean)


def _generate_expose(idea: BookIdea, session: CreativeSession) -> str:
    """Generiert ein wissenschaftliches Exposé (Forschungsfrage, Stand, Methodik, Relevanz)."""
    router = _get_router()
    field_hint = f"Fachgebiet: {session.research_field}" if session.research_field else ""
    logline = idea.refined_logline or idea.logline
    system = (
        "Du bist ein erfahrener Wissenschaftsberater. "
        "Erstelle ein kompaktes wissenschaftliches Exposé.\n"
        "Antworte nur mit dem Exposé-Text, kein JSON, keine Erklärungen."
    )
    user = (
        f"Thema: {idea.title}\n"
        f"Forschungsfrage: {logline}\n"
        f"Innovationsbeitrag: {idea.hook}\n"
        f"Schlüsselkonzepte: {', '.join(idea.themes or [])}\n"
        f"{field_hint}\n\n"
        "Erstelle ein wissenschaftliches Exposé (250-400 Wörter) mit: "
        "Forschungsfrage, Forschungsstand, Methodik, erwarteter Beitrag zur Forschung, "
        "Gliederungsvorschlag."
    )
    return router.completion(action_code="outline_generate", messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ])


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
    return router.completion(action_code="outline_generate", messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ])
