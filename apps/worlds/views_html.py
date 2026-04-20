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
            ProjectWorldLink.objects.filter(project__owner=self.request.user)
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
    Detail-Ansicht: Welt + ihre Charaktere + Orte.
    Primär: lokale Daten (ProjectCharacterLink/ProjectLocationLink).
    Sekundär: WeltenHub-Anreicherung wenn verfügbar.
    """

    template_name = "worlds/world_detail.html"

    def get(self, request, pk):
        from apps.worlds.models import ProjectCharacterLink, ProjectLocationLink

        link = get_object_or_404(ProjectWorldLink, pk=pk, project__owner=request.user)

        # WeltenHub optional laden
        world = None
        weltenhub_available = False
        wh_chars = {}
        wh_locs = {}
        if link.weltenhub_world_id:
            try:
                from weltenfw.django import get_client

                client = get_client()
                world = client.worlds.get(link.weltenhub_world_id)
                weltenhub_available = True
                # Cache world name locally
                if world and getattr(world, "name", None) and not link.name:
                    link.name = world.name
                    link.save(update_fields=["name"])
                # WeltenHub-Daten als Enrichment
                from apps.worlds.services import WorldCharacterService, WorldLocationService

                for c in WorldCharacterService().get_world_characters(link.weltenhub_world_id):
                    wh_chars[str(c.id)] = c
                for loc in WorldLocationService().get_world_locations(link.weltenhub_world_id):
                    wh_locs[str(loc.id)] = loc
            except Exception as exc:
                logger.warning("ProjectWorldDetailView: WeltenHub nicht erreichbar: %s", exc)
                messages.warning(request, "WeltenHub derzeit nicht erreichbar.")

        # Lokale Charaktere — primäre Datenquelle
        local_chars = ProjectCharacterLink.objects.filter(project=link.project)
        enriched_chars = []
        for pcl in local_chars:
            wh_char = wh_chars.get(str(pcl.weltenhub_character_id)) if pcl.weltenhub_character_id else None
            enriched_chars.append(
                {
                    "pcl": pcl,
                    "pcl_pk": str(pcl.pk),
                    "name": pcl.name or (wh_char.name if wh_char else "Unbekannt"),
                    "personality": pcl.personality or (getattr(wh_char, "personality", "") if wh_char else ""),
                    "backstory": pcl.backstory or (getattr(wh_char, "backstory", "") if wh_char else ""),
                    "is_protagonist": pcl.is_protagonist
                    or (getattr(wh_char, "is_protagonist", False) if wh_char else False),
                    "narrative_role": pcl.get_narrative_role_display(),
                    "narrative_role_key": pcl.narrative_role,
                    "voice_pattern": pcl.voice_pattern,
                    "secret_what": pcl.secret_what,
                    "character_status": pcl.get_character_status_display(),
                    "first_appearance": pcl.first_appearance,
                    "source": pcl.source,
                }
            )

        # Lokale Orte — primäre Datenquelle
        local_locs = ProjectLocationLink.objects.filter(project=link.project)
        enriched_locs = []
        for pll in local_locs:
            wh_loc = wh_locs.get(str(pll.weltenhub_location_id)) if pll.weltenhub_location_id else None
            enriched_locs.append(
                {
                    "pll": pll,
                    "pll_pk": str(pll.pk),
                    "name": pll.name or (wh_loc.name if wh_loc else "Unbekannt"),
                    "description": pll.description or (getattr(wh_loc, "description", "") if wh_loc else ""),
                    "atmosphere": pll.atmosphere or (getattr(wh_loc, "atmosphere", "") if wh_loc else ""),
                    "source": pll.source,
                }
            )

        # Outline vorhanden?
        from apps.projects.models import OutlineVersion

        has_outline = OutlineVersion.objects.filter(project=link.project, is_active=True).exists()

        world_display_name = link.name or (world.name if world else None) or link.project.title

        return render(
            request,
            self.template_name,
            {
                "link": link,
                "world": world,
                "world_display_name": world_display_name,
                "weltenhub_available": weltenhub_available,
                "characters": enriched_chars,
                "locations": enriched_locs,
                "project": link.project,
                "has_outline": has_outline,
            },
        )


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
            messages.success(request, f"Welt \u201e{result.name}\u201c in WeltenHub erstellt und verknüpft.")
        else:
            messages.error(request, "Welt generiert, aber WeltenHub-Speicherung fehlgeschlagen.")
        return redirect("worlds_html:list")


class WorldCharacterGenerateView(LoginRequiredMixin, View):
    """
    POST: Charaktere per LLM generieren.
    Speichert in WeltenHub wenn verfügbar, sonst lokal.
    """

    def post(self, request, pk):
        from apps.worlds.models import ProjectCharacterLink
        from apps.worlds.services import WorldCharacterService

        link = get_object_or_404(ProjectWorldLink, pk=pk, project__owner=request.user)
        count = int(request.POST.get("count", 5))
        svc = WorldCharacterService()
        result = svc.generate_cast(
            weltenhub_world_id=link.weltenhub_world_id or "00000000-0000-0000-0000-000000000000",
            project_id=str(link.project_id),
            count=count,
            requirements=request.POST.get("requirements", ""),
        )
        if not result.success:
            messages.error(request, f"Charakter-Generierung fehlgeschlagen: {result.error}")
            return redirect("worlds_html:detail", pk=pk)

        # Versuche WeltenHub, Fallback auf lokal
        saved_to_wh = False
        if link.weltenhub_world_id:
            try:
                ids = svc.save_to_weltenhub(link.weltenhub_world_id, result.characters)
                svc.link_to_project(str(link.project_id), ids)
                saved_to_wh = True
                messages.success(request, f"{len(ids)} Charaktere in WeltenHub erstellt.")
            except Exception as exc:
                logger.warning("WeltenHub save failed, saving locally: %s", exc)

        if not saved_to_wh:
            created = 0
            for char_data in result.characters:
                name = char_data.get("name", "").strip()
                if not name:
                    continue
                ProjectCharacterLink.objects.create(
                    project=link.project,
                    name=name,
                    description=char_data.get("description", ""),
                    personality=char_data.get("personality", ""),
                    backstory=char_data.get("backstory", ""),
                    is_protagonist=char_data.get("is_protagonist", False),
                    narrative_role="protagonist" if char_data.get("is_protagonist") else "supporting",
                    source="llm",
                )
                created += 1
            messages.success(request, f"{created} Charaktere lokal erstellt.")

        return redirect("worlds_html:detail", pk=pk)


class WorldLocationGenerateView(LoginRequiredMixin, View):
    """
    POST: Orte per LLM generieren.
    Speichert in WeltenHub wenn verfügbar, sonst lokal.
    """

    def post(self, request, pk):
        from apps.worlds.models import ProjectLocationLink
        from apps.worlds.services import WorldLocationService

        link = get_object_or_404(ProjectWorldLink, pk=pk, project__owner=request.user)
        count = int(request.POST.get("count", 5))
        svc = WorldLocationService()
        result = svc.generate_locations(
            weltenhub_world_id=link.weltenhub_world_id or "00000000-0000-0000-0000-000000000000",
            project_id=str(link.project_id),
            count=count,
            requirements=request.POST.get("requirements", ""),
        )
        if not result.success:
            messages.error(request, f"Ort-Generierung fehlgeschlagen: {result.error}")
            return redirect("worlds_html:detail", pk=pk)

        # Versuche WeltenHub, Fallback auf lokal
        saved_to_wh = False
        if link.weltenhub_world_id:
            try:
                ids = svc.save_to_weltenhub(link.weltenhub_world_id, result.locations)
                svc.link_to_project(str(link.project_id), ids)
                saved_to_wh = True
                messages.success(request, f"{len(ids)} Orte in WeltenHub erstellt.")
            except Exception as exc:
                logger.warning("WeltenHub location save failed, saving locally: %s", exc)

        if not saved_to_wh:
            created = 0
            for loc_data in result.locations:
                name = loc_data.get("name", "").strip()
                if not name:
                    continue
                ProjectLocationLink.objects.create(
                    project=link.project,
                    name=name,
                    description=loc_data.get("description", ""),
                    atmosphere=loc_data.get("atmosphere", ""),
                    significance=loc_data.get("significance", ""),
                    source="llm",
                )
                created += 1
            messages.success(request, f"{created} Orte lokal erstellt.")

        return redirect("worlds_html:detail", pk=pk)


class CharacterCreateView(LoginRequiredMixin, View):
    """
    GET:  Formular zum manuellen Erstellen eines Charakters.
    POST: Charakter in WeltenHub anlegen + mit Projekt verknüpfen.
    """

    template_name = "worlds/character_create.html"

    def get(self, request, pk):
        link = get_object_or_404(ProjectWorldLink, pk=pk, project__owner=request.user)
        world = None
        try:
            from weltenfw.django import get_client

            world = get_client().worlds.get(link.weltenhub_world_id)
        except Exception:
            pass
        return render(
            request,
            self.template_name,
            {
                "link": link,
                "world": world,
                "project": link.project,
            },
        )

    def post(self, request, pk):
        from apps.worlds.services import WorldCharacterService

        link = get_object_or_404(ProjectWorldLink, pk=pk, project__owner=request.user)
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

        from apps.worlds.models import ProjectCharacterLink

        saved_to_wh = False
        try:
            svc = WorldCharacterService()
            saved_ids = svc.save_to_weltenhub(link.weltenhub_world_id, [char_data])
            if saved_ids:
                svc.link_to_project(str(link.project_id), saved_ids)
                pcl = ProjectCharacterLink.objects.filter(
                    project=link.project, weltenhub_character_id=saved_ids[0]
                ).first()
                if pcl:
                    pcl.name = name
                    pcl.description = char_data.get("personality") or ""
                    pcl.personality = char_data.get("personality") or ""
                    pcl.backstory = char_data.get("backstory") or ""
                    pcl.narrative_role = "protagonist" if char_data["is_protagonist"] else "supporting"
                    pcl.voice_pattern = request.POST.get("voice_pattern", "").strip()
                    pcl.secret_what = request.POST.get("secret_what", "").strip()
                    pcl.secret_from_whom = request.POST.get("secret_from_whom", "").strip()
                    pcl.secret_why = request.POST.get("secret_why", "").strip()
                    pcl.source = "manual"
                    pcl.save()
                saved_to_wh = True
        except Exception as exc:
            logger.warning("CharacterCreateView: WeltenHub save failed: %s", exc)

        if not saved_to_wh:
            ProjectCharacterLink.objects.create(
                project=link.project,
                name=name,
                description=char_data.get("personality") or "",
                personality=char_data.get("personality") or "",
                backstory=char_data.get("backstory") or "",
                is_protagonist=char_data["is_protagonist"],
                narrative_role="protagonist" if char_data["is_protagonist"] else "supporting",
                voice_pattern=request.POST.get("voice_pattern", "").strip(),
                secret_what=request.POST.get("secret_what", "").strip(),
                source="manual",
            )

        messages.success(request, f"Charakter \u201e{name}\u201c erstellt.")
        return redirect("worlds_html:detail", pk=pk)


class CharacterLinkView(LoginRequiredMixin, View):
    """
    GET:  Zeigt alle Charaktere der Welt aus WeltenHub — bereits verknüpfte markiert.
    POST: Ausgewählte Charaktere mit Projekt verknüpfen.
    """

    template_name = "worlds/character_link.html"

    def get(self, request, pk):
        link = get_object_or_404(ProjectWorldLink, pk=pk, project__owner=request.user)
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
                ProjectCharacterLink.objects.filter(project=link.project).values_list(
                    "weltenhub_character_id", flat=True
                )
            )
        except Exception as exc:
            logger.warning("CharacterLinkView: WeltenHub nicht erreichbar: %s", exc)
            messages.warning(request, "WeltenHub derzeit nicht erreichbar.")

        return render(
            request,
            self.template_name,
            {
                "link": link,
                "world": world,
                "project": link.project,
                "all_characters": all_characters,
                "linked_ids": linked_ids,
            },
        )

    def post(self, request, pk):
        from uuid import UUID
        from apps.worlds.services import WorldCharacterService

        link = get_object_or_404(ProjectWorldLink, pk=pk, project__owner=request.user)
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


class CharacterDetailView(LoginRequiredMixin, View):
    """
    GET:  Charakter-Detailseite mit allen Feldern + Edit-Formular.
    POST: Speichert editierte lokale Felder (ProjectCharacterLink).
    """

    template_name = "worlds/character_detail.html"

    def _load_context(self, request, pcl_pk):
        from apps.worlds.models import ProjectCharacterLink

        pcl = get_object_or_404(ProjectCharacterLink, pk=pcl_pk, project__owner=request.user)
        # Load WeltenHub character data (graceful degradation)
        char = None
        try:
            char = pcl.get_character()
        except Exception as exc:
            logger.warning("CharacterDetailView: WeltenHub nicht erreichbar: %s", exc)

        # Find the world link for back-navigation
        world_link = ProjectWorldLink.objects.filter(project=pcl.project).first()
        return pcl, char, world_link

    def get(self, request, pk):
        pcl, char, world_link = self._load_context(request, pk)

        # Load relationships (bidirectional)
        from apps.worlds.models import CharacterRelationship

        rels_from = CharacterRelationship.objects.filter(from_character=pcl).select_related("to_character")
        rels_to = CharacterRelationship.objects.filter(to_character=pcl).select_related("from_character")

        # All other characters in this project (for relationship dropdown)
        from apps.worlds.models import ProjectCharacterLink

        other_characters = ProjectCharacterLink.objects.filter(project=pcl.project).exclude(pk=pcl.pk)

        display_name = pcl.name or (char.name if char else None) or ""

        return render(
            request,
            self.template_name,
            {
                "pcl": pcl,
                "char": char,
                "display_name": display_name,
                "world_link": world_link,
                "project": pcl.project,
                "narrative_roles": pcl.NARRATIVE_ROLES,
                "antagonist_types": pcl.ANTAGONIST_TYPES,
                "character_statuses": pcl.CHARACTER_STATUS,
                "rels_from": rels_from,
                "rels_to": rels_to,
                "other_characters": other_characters,
                "relationship_types": CharacterRelationship.RELATIONSHIP_TYPES,
            },
        )

    def post(self, request, pk):
        from apps.worlds.models import ProjectCharacterLink

        pcl = get_object_or_404(ProjectCharacterLink, pk=pk, project__owner=request.user)

        # Update all editable local fields
        field_map = {
            "name": ("name", str),
            "description": ("description", str),
            "personality": ("personality", str),
            "backstory": ("backstory", str),
            "narrative_role": ("narrative_role", str),
            "want": ("want", str),
            "need": ("need", str),
            "flaw": ("flaw", str),
            "ghost": ("ghost", str),
            "false_belief": ("false_belief", str),
            "true_belief": ("true_belief", str),
            "voice_pattern": ("voice_pattern", str),
            "secret_what": ("secret_what", str),
            "secret_from_whom": ("secret_from_whom", str),
            "secret_why": ("secret_why", str),
            "character_status": ("character_status", str),
            "first_appearance": ("first_appearance", str),
            "project_arc": ("project_arc", str),
            "project_role": ("project_role", str),
            "notes": ("notes", str),
            "antagonist_type": ("antagonist_type", str),
            "antagonist_logic": ("antagonist_logic", str),
            "mirror_to_protagonist": ("mirror_to_protagonist", str),
            "shared_trait_with_protagonist": ("shared_trait_with_protagonist", str),
            "information_advantage": ("information_advantage", str),
        }

        updated = []
        for form_name, (model_field, _) in field_map.items():
            val = request.POST.get(form_name, "").strip()
            if getattr(pcl, model_field) != val:
                setattr(pcl, model_field, val)
                updated.append(model_field)

        if updated:
            pcl.save(update_fields=updated)
            messages.success(request, f"Charakter aktualisiert ({len(updated)} Felder).")
        else:
            messages.info(request, "Keine Änderungen erkannt.")

        return redirect("worlds_html:character_detail", pk=pk)


class RelationshipAddView(LoginRequiredMixin, View):
    """POST: Neue Beziehung zwischen zwei Charakteren anlegen."""

    def post(self, request, pk):
        from apps.worlds.models import ProjectCharacterLink, CharacterRelationship

        pcl = get_object_or_404(ProjectCharacterLink, pk=pk, project__owner=request.user)
        to_pk = request.POST.get("to_character")
        rel_type = request.POST.get("relationship_type", "knows")
        description = request.POST.get("description", "").strip()
        since_chapter = request.POST.get("since_chapter", "").strip()

        if not to_pk:
            messages.warning(request, "Bitte Zielcharakter auswählen.")
            return redirect("worlds_html:character_detail", pk=pk)

        to_char = get_object_or_404(ProjectCharacterLink, pk=to_pk, project=pcl.project)

        _, created = CharacterRelationship.objects.get_or_create(
            project=pcl.project,
            from_character=pcl,
            to_character=to_char,
            relationship_type=rel_type,
            defaults={
                "description": description,
                "since_chapter": since_chapter,
            },
        )
        if created:
            messages.success(
                request,
                f"Beziehung \u201e{dict(CharacterRelationship.RELATIONSHIP_TYPES).get(rel_type, rel_type)}\u201c hinzugefügt.",
            )
        else:
            messages.info(request, "Diese Beziehung existiert bereits.")

        return redirect("worlds_html:character_detail", pk=pk)


class RelationshipDeleteView(LoginRequiredMixin, View):
    """POST: Beziehung löschen."""

    def post(self, request, pk):
        from apps.worlds.models import CharacterRelationship

        rel = get_object_or_404(CharacterRelationship, pk=pk)
        char_pk = rel.from_character.pk
        if rel.project.owner != request.user:
            messages.error(request, "Keine Berechtigung.")
            return redirect("worlds_html:list")

        rel.delete()
        messages.success(request, "Beziehung entfernt.")
        return redirect("worlds_html:character_detail", pk=char_pk)


class OutlineExtractView(LoginRequiredMixin, View):
    """
    POST: Charaktere + Orte aus Outline-Nodes extrahieren (LLM oder Regex-Fallback).
    Erstellt lokale ProjectCharacterLink/ProjectLocationLink-Einträge.
    """

    def post(self, request, pk):
        from apps.worlds.services import extract_from_outline, save_extracted_to_project

        link = get_object_or_404(ProjectWorldLink, pk=pk, project__owner=request.user)
        extracted = extract_from_outline(link.project)
        counts = save_extracted_to_project(link.project, extracted, world_link=link)

        char_count = counts["characters_created"]
        loc_count = counts["locations_created"]
        if char_count or loc_count:
            messages.success(
                request,
                f"Aus Outline extrahiert: {char_count} Charakter(e), {loc_count} Ort(e).",
            )
        else:
            messages.info(request, "Keine neuen Charaktere oder Orte im Outline gefunden.")
        return redirect("worlds_html:detail", pk=pk)


class CharacterRefineView(LoginRequiredMixin, View):
    """POST: Einen Charakter per KI verfeinern (lokale Daten anreichern)."""

    def post(self, request, pk):
        from apps.worlds.models import ProjectCharacterLink
        from apps.worlds.services import refine_character_with_llm

        pcl = get_object_or_404(ProjectCharacterLink, pk=pk, project__owner=request.user)
        ok = refine_character_with_llm(pcl)
        if ok:
            messages.success(request, f'Charakter „{pcl.name}" per KI verfeinert.')
        else:
            messages.error(request, "KI-Verfeinerung fehlgeschlagen.")
        return redirect("worlds_html:character_detail", pk=pk)


class LocationDetailView(LoginRequiredMixin, View):
    """
    GET:  Ort-Detailseite mit allen Feldern + Edit-Formular.
    POST: Speichert editierte lokale Felder (ProjectLocationLink).
    """

    template_name = "worlds/location_detail.html"

    def get(self, request, pk):
        from apps.worlds.models import ProjectLocationLink

        pll = get_object_or_404(ProjectLocationLink, pk=pk, project__owner=request.user)
        world_link = ProjectWorldLink.objects.filter(project=pll.project).first()
        return render(
            request,
            self.template_name,
            {
                "pll": pll,
                "world_link": world_link,
                "project": pll.project,
            },
        )

    def post(self, request, pk):
        from apps.worlds.models import ProjectLocationLink

        pll = get_object_or_404(ProjectLocationLink, pk=pk, project__owner=request.user)

        field_map = {
            "name": ("name", str),
            "description": ("description", str),
            "atmosphere": ("atmosphere", str),
            "significance": ("significance", str),
            "notes": ("notes", str),
        }

        updated = []
        for form_name, (model_field, _) in field_map.items():
            val = request.POST.get(form_name, "").strip()
            if getattr(pll, model_field) != val:
                setattr(pll, model_field, val)
                updated.append(model_field)

        if updated:
            pll.save(update_fields=updated)
            messages.success(request, f"Ort aktualisiert ({len(updated)} Felder).")
        else:
            messages.info(request, "Keine Änderungen erkannt.")

        return redirect("worlds_html:location_detail", pk=pk)


class LocationRefineView(LoginRequiredMixin, View):
    """POST: Einen Ort per KI verfeinern (lokale Daten anreichern)."""

    def post(self, request, pk):
        from apps.worlds.models import ProjectLocationLink
        from apps.worlds.services import refine_location_with_llm

        pll = get_object_or_404(ProjectLocationLink, pk=pk, project__owner=request.user)
        ok = refine_location_with_llm(pll)
        if ok:
            messages.success(request, f'Ort „{pll.name}" per KI verfeinert.')
        else:
            messages.error(request, "KI-Verfeinerung fehlgeschlagen.")

        return redirect("worlds_html:location_detail", pk=pk)
