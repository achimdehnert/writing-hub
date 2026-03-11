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
