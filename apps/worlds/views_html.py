"""
Worlds — HTML Frontend Views

Lädt Welt-/Charakter-/Orts-Daten live aus WeltenHub (iil-weltenfw)
und zeigt sie im Writing-Hub-Kontext an.
"""
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView

from .models import ProjectWorldLink

logger = logging.getLogger(__name__)


class WorldListView(LoginRequiredMixin, ListView):
    """
    Übersicht aller verknüpften Welten + Live-Daten aus WeltenHub.
    """
    model = ProjectWorldLink
    template_name = "worlds/world_list.html"
    context_object_name = "world_links"

    def get_queryset(self):
        return (
            ProjectWorldLink.objects
            .filter(project__owner=self.request.user)
            .select_related("project")
            .order_by("project__title", "role")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["total"] = self.get_queryset().count()

        # WeltenHub-Daten für jede verknüpfte Welt nachladen
        enriched = []
        try:
            from weltenfw.django import get_client
            client = get_client()
            for link in ctx["world_links"]:
                try:
                    world = client.worlds.get(link.weltenhub_world_id)
                    enriched.append({"link": link, "world": world})
                except Exception:
                    enriched.append({"link": link, "world": None})
        except Exception:
            for link in ctx["world_links"]:
                enriched.append({"link": link, "world": None})
        ctx["enriched_worlds"] = enriched
        return ctx


class ProjectWorldDetailView(LoginRequiredMixin, View):
    """
    Detail-Ansicht: Welt + ihre Charaktere + Orte aus WeltenHub.
    """
    template_name = "worlds/world_detail.html"

    def get(self, request, pk):
        link = get_object_or_404(
            ProjectWorldLink, pk=pk, project__owner=request.user
        )
        world = None
        characters = []
        locations = []
        try:
            from weltenfw.django import get_client
            from apps.worlds.services import WorldCharacterService, WorldLocationService
            client = get_client()
            world = client.worlds.get(link.weltenhub_world_id)
            characters = WorldCharacterService().get_world_characters(link.weltenhub_world_id)
            locations = WorldLocationService().get_world_locations(link.weltenhub_world_id)
        except Exception as exc:
            logger.warning("ProjectWorldDetailView: WeltenHub nicht erreichbar: %s", exc)
            messages.warning(request, "WeltenHub derzeit nicht erreichbar.")
        return render(request, self.template_name, {
            "link": link,
            "world": world,
            "characters": characters,
            "locations": locations,
            "project": link.project,
        })


class WorldGenerateView(LoginRequiredMixin, View):
    """
    POST: Neue Welt per LLM generieren + in WeltenHub speichern + Projekt verknüpfen.
    """
    def post(self, request):
        from apps.projects.models import BookProject
        from apps.worlds.services import WorldBuilderService

        project_id = request.POST.get("project_id")
        project = get_object_or_404(BookProject, pk=project_id, owner=request.user)

        svc = WorldBuilderService()
        result = svc.generate_world(
            project_id=str(project.pk),
            genre=request.POST.get("genre", ""),
            tone=request.POST.get("tone", ""),
            keywords=[k.strip() for k in request.POST.get("keywords", "").split(",") if k.strip()],
        )
        if not result.success:
            messages.error(request, f"Weltgenerierung fehlgeschlagen: {result.error}")
            return redirect("worlds_html:list")

        world_id = svc.save_to_weltenhub(result)
        if world_id:
            svc.link_to_project(str(project.pk), world_id)
            messages.success(request, f'Welt \u201e{result.name}\u201c in WeltenHub erstellt und verknüpft.')
        else:
            messages.error(request, "Welt generiert, aber WeltenHub-Speicherung fehlgeschlagen.")
        return redirect("worlds_html:list")


class WorldCharacterGenerateView(LoginRequiredMixin, View):
    """
    POST: Charaktere für eine Welt per LLM generieren + in WeltenHub speichern.
    """
    def post(self, request, pk):
        from apps.worlds.services import WorldCharacterService

        link = get_object_or_404(
            ProjectWorldLink, pk=pk, project__owner=request.user
        )
        count = int(request.POST.get("count", 5))
        svc = WorldCharacterService()
        result = svc.generate_cast(
            weltenhub_world_id=link.weltenhub_world_id,
            project_id=str(link.project_id),
            count=count,
            requirements=request.POST.get("requirements", ""),
        )
        if not result.success:
            messages.error(request, f"Charakter-Generierung fehlgeschlagen: {result.error}")
        else:
            ids = svc.save_to_weltenhub(link.weltenhub_world_id, result.characters)
            svc.link_to_project(str(link.project_id), ids)
            messages.success(request, f"{len(ids)} Charaktere in WeltenHub erstellt.")
        return redirect("worlds_html:detail", pk=pk)


class WorldLocationGenerateView(LoginRequiredMixin, View):
    """
    POST: Orte für eine Welt per LLM generieren + in WeltenHub speichern.
    """
    def post(self, request, pk):
        from apps.worlds.services import WorldLocationService

        link = get_object_or_404(
            ProjectWorldLink, pk=pk, project__owner=request.user
        )
        count = int(request.POST.get("count", 5))
        svc = WorldLocationService()
        result = svc.generate_locations(
            weltenhub_world_id=link.weltenhub_world_id,
            project_id=str(link.project_id),
            count=count,
            requirements=request.POST.get("requirements", ""),
        )
        if not result.success:
            messages.error(request, f"Ort-Generierung fehlgeschlagen: {result.error}")
        else:
            ids = svc.save_to_weltenhub(link.weltenhub_world_id, result.locations)
            svc.link_to_project(str(link.project_id), ids)
            messages.success(request, f"{len(ids)} Orte in WeltenHub erstellt.")
        return redirect("worlds_html:detail", pk=pk)


class CharacterCreateView(LoginRequiredMixin, View):
    """
    GET:  Formular zum manuellen Erstellen eines Charakters.
    POST: Charakter in WeltenHub anlegen + mit Projekt verknüpfen.
    """
    template_name = "worlds/character_create.html"

    def get(self, request, pk):
        link = get_object_or_404(
            ProjectWorldLink, pk=pk, project__owner=request.user
        )
        world = None
        try:
            from weltenfw.django import get_client
            world = get_client().worlds.get(link.weltenhub_world_id)
        except Exception:
            pass
        return render(request, self.template_name, {
            "link": link,
            "world": world,
            "project": link.project,
        })

    def post(self, request, pk):
        from apps.worlds.services import WorldCharacterService

        link = get_object_or_404(
            ProjectWorldLink, pk=pk, project__owner=request.user
        )
        name = request.POST.get("name", "").strip()
        if not name:
            messages.error(request, "Name ist erforderlich.")
            return redirect("worlds_html:character_create", pk=pk)

        char_data = {
            "name": name,
            "personality": request.POST.get("personality", "").strip() or None,
            "backstory": request.POST.get("backstory", "").strip() or None,
            "goals": request.POST.get("goals", "").strip() or None,
            "fears": request.POST.get("fears", "").strip() or None,
            "appearance": request.POST.get("appearance", "").strip() or None,
            "is_protagonist": request.POST.get("is_protagonist") == "on",
            "notes": request.POST.get("notes", "").strip() or None,
        }

        svc = WorldCharacterService()
        saved_ids = svc.save_to_weltenhub(link.weltenhub_world_id, [char_data])
        if saved_ids:
            svc.link_to_project(str(link.project_id), saved_ids)
            messages.success(request, f'Charakter „{name}" erstellt und verknüpft.')
        else:
            messages.error(request, "Charakter konnte nicht in WeltenHub erstellt werden.")
        return redirect("worlds_html:detail", pk=pk)


class CharacterLinkView(LoginRequiredMixin, View):
    """
    GET:  Zeigt alle Charaktere der Welt aus WeltenHub — bereits verknüpfte markiert.
    POST: Ausgewählte Charaktere mit Projekt verknüpfen.
    """
    template_name = "worlds/character_link.html"

    def get(self, request, pk):
        link = get_object_or_404(
            ProjectWorldLink, pk=pk, project__owner=request.user
        )
        world = None
        all_characters = []
        linked_ids = set()
        try:
            from weltenfw.django import get_client
            from apps.worlds.services import WorldCharacterService
            from apps.worlds.models import ProjectCharacterLink

            client = get_client()
            world = client.worlds.get(link.weltenhub_world_id)
            all_characters = WorldCharacterService().get_world_characters(link.weltenhub_world_id)

            linked_ids = set(
                ProjectCharacterLink.objects.filter(
                    project=link.project
                ).values_list("weltenhub_character_id", flat=True)
            )
        except Exception as exc:
            logger.warning("CharacterLinkView: WeltenHub nicht erreichbar: %s", exc)
            messages.warning(request, "WeltenHub derzeit nicht erreichbar.")

        return render(request, self.template_name, {
            "link": link,
            "world": world,
            "project": link.project,
            "all_characters": all_characters,
            "linked_ids": linked_ids,
        })

    def post(self, request, pk):
        from uuid import UUID
        from apps.worlds.services import WorldCharacterService

        link = get_object_or_404(
            ProjectWorldLink, pk=pk, project__owner=request.user
        )
        selected = request.POST.getlist("character_ids")
        if not selected:
            messages.warning(request, "Keine Charaktere ausgewählt.")
            return redirect("worlds_html:character_link", pk=pk)

        char_ids = []
        for cid in selected:
            try:
                char_ids.append(UUID(cid))
            except (ValueError, TypeError):
                continue

        svc = WorldCharacterService()
        count = svc.link_to_project(str(link.project_id), char_ids)
        messages.success(request, f"{count} Charakter(e) mit Projekt verknüpft.")
        return redirect("worlds_html:detail", pk=pk)
