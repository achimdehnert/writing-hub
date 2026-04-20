"""
Worlds API Views — writing-hub

Lokale Daten (ProjectWorldLink, ProjectCharacterLink, ProjectLocationLink) als primaere Quelle.
WeltenHub-Enrichment optional (graceful degradation bei fehlendem Token).
"""

import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ProjectCharacterLink, ProjectLocationLink, ProjectWorldLink
from .serializers import (
    ProjectCharacterLinkSerializer,
    ProjectLocationLinkSerializer,
    ProjectWorldLinkSerializer,
)

logger = logging.getLogger(__name__)


class WorldListView(APIView):
    """
    GET  /worlds/?project=<id>  — ProjectWorldLinks des Users
    POST /worlds/               — Neue Welt per LLM generieren
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = (
            ProjectWorldLink.objects.filter(project__owner=request.user)
            .select_related("project")
            .order_by("-created_at")
        )

        project_id = request.query_params.get("project")
        if project_id:
            qs = qs.filter(project_id=project_id)

        serializer = ProjectWorldLinkSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        project_id = request.data.get("project_id")
        if not project_id:
            return Response({"detail": "project_id erforderlich."}, status=status.HTTP_400_BAD_REQUEST)

        from apps.worlds.services import WorldBuilderService

        svc = WorldBuilderService()
        result = svc.generate_world(
            project_id=project_id,
            genre=request.data.get("genre", ""),
            tone=request.data.get("tone", ""),
            keywords=request.data.get("keywords", []),
        )
        if not result.success:
            return Response({"detail": result.error}, status=status.HTTP_502_BAD_GATEWAY)

        world_id = None
        try:
            world_id = svc.save_to_weltenhub(result)
        except Exception as exc:
            logger.warning("WeltenHub save failed: %s", exc)

        if world_id:
            svc.link_to_project(project_id, world_id)

        return Response(
            {
                "name": result.name,
                "description": result.description,
                "weltenhub_world_id": str(world_id) if world_id else None,
            },
            status=status.HTTP_201_CREATED,
        )


class WorldDetailView(APIView):
    """
    GET /worlds/<pk>/ — Welt-Details (lokal + optional WeltenHub)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        link = get_object_or_404(ProjectWorldLink, pk=pk, project__owner=request.user)
        data = ProjectWorldLinkSerializer(link).data

        # WeltenHub enrichment
        if link.weltenhub_world_id:
            try:
                from weltenfw.django import get_client

                world = get_client().worlds.get(link.weltenhub_world_id)
                data["weltenhub"] = {
                    "name": world.name,
                    "description": world.description or "",
                    "geography": getattr(world, "geography", "") or "",
                    "magic_system": getattr(world, "magic_system", "") or "",
                    "history": getattr(world, "history", "") or "",
                }
            except Exception as exc:
                logger.warning("WorldDetailView: WeltenHub nicht erreichbar: %s", exc)
                data["weltenhub"] = None

        # Lokale Charaktere + Orte
        data["characters"] = ProjectCharacterLinkSerializer(
            ProjectCharacterLink.objects.filter(project=link.project),
            many=True,
        ).data
        data["locations"] = ProjectLocationLinkSerializer(
            ProjectLocationLink.objects.filter(project=link.project),
            many=True,
        ).data

        return Response(data)


class WorldCharacterListView(APIView):
    """
    GET  /worlds/<pk>/characters/           — Lokale Charaktere des Projekts
    POST /worlds/<pk>/characters/generate/  — Per LLM generieren (lokal + optional WeltenHub)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, world_pk):
        link = get_object_or_404(ProjectWorldLink, pk=world_pk, project__owner=request.user)
        chars = ProjectCharacterLink.objects.filter(project=link.project)
        serializer = ProjectCharacterLinkSerializer(chars, many=True)
        return Response(serializer.data)

    def post(self, request, world_pk):
        link = get_object_or_404(ProjectWorldLink, pk=world_pk, project__owner=request.user)
        count = int(request.data.get("count", 5))

        from apps.worlds.services import WorldCharacterService

        svc = WorldCharacterService()
        result = svc.generate_cast(
            weltenhub_world_id=str(link.weltenhub_world_id or "00000000-0000-0000-0000-000000000000"),
            project_id=str(link.project_id),
            count=count,
            requirements=request.data.get("requirements", ""),
        )
        if not result.success:
            return Response({"detail": result.error}, status=status.HTTP_502_BAD_GATEWAY)

        # WeltenHub save attempt → fallback local
        saved_to_wh = False
        saved_ids = []
        if link.weltenhub_world_id:
            try:
                saved_ids = svc.save_to_weltenhub(str(link.weltenhub_world_id), result.characters)
                svc.link_to_project(str(link.project_id), saved_ids)
                saved_to_wh = True
            except Exception as exc:
                logger.warning("WeltenHub character save failed: %s", exc)

        if not saved_to_wh:
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

        return Response(
            {
                "generated": len(result.characters),
                "saved_to_weltenhub": saved_to_wh,
                "characters": result.characters,
            },
            status=status.HTTP_201_CREATED,
        )


class WorldLocationListView(APIView):
    """
    GET  /worlds/<pk>/locations/           — Lokale Orte des Projekts
    POST /worlds/<pk>/locations/generate/  — Per LLM generieren
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, world_pk):
        link = get_object_or_404(ProjectWorldLink, pk=world_pk, project__owner=request.user)
        locs = ProjectLocationLink.objects.filter(project=link.project)
        serializer = ProjectLocationLinkSerializer(locs, many=True)
        return Response(serializer.data)

    def post(self, request, world_pk):
        link = get_object_or_404(ProjectWorldLink, pk=world_pk, project__owner=request.user)
        count = int(request.data.get("count", 5))

        from apps.worlds.services import WorldLocationService

        svc = WorldLocationService()
        result = svc.generate_locations(
            weltenhub_world_id=str(link.weltenhub_world_id or "00000000-0000-0000-0000-000000000000"),
            project_id=str(link.project_id),
            count=count,
            requirements=request.data.get("requirements", ""),
        )
        if not result.success:
            return Response({"detail": result.error}, status=status.HTTP_502_BAD_GATEWAY)

        saved_to_wh = False
        if link.weltenhub_world_id:
            try:
                ids = svc.save_to_weltenhub(str(link.weltenhub_world_id), result.locations)
                svc.link_to_project(str(link.project_id), ids)
                saved_to_wh = True
            except Exception as exc:
                logger.warning("WeltenHub location save failed: %s", exc)

        if not saved_to_wh:
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

        return Response(
            {
                "generated": len(result.locations),
                "saved_to_weltenhub": saved_to_wh,
                "locations": result.locations,
            },
            status=status.HTTP_201_CREATED,
        )


class OutlineExtractView(APIView):
    """
    POST /worlds/<pk>/outline-extract/  — Charaktere + Orte aus Outline extrahieren
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        link = get_object_or_404(ProjectWorldLink, pk=pk, project__owner=request.user)

        from apps.worlds.services import extract_from_outline, save_extracted_to_project

        extracted = extract_from_outline(link.project)
        counts = save_extracted_to_project(link.project, extracted, world_link=link)

        return Response(
            {
                "characters_created": counts["characters_created"],
                "locations_created": counts["locations_created"],
                "extracted": extracted,
            },
            status=status.HTTP_201_CREATED,
        )


class CharacterRefineView(APIView):
    """
    POST /worlds/characters/<pk>/refine/  — Charakter per KI verfeinern
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        pcl = get_object_or_404(ProjectCharacterLink, pk=pk, project__owner=request.user)

        from apps.worlds.services import refine_character_with_llm

        ok = refine_character_with_llm(pcl)
        if not ok:
            return Response(
                {"detail": "KI-Verfeinerung fehlgeschlagen."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        pcl.refresh_from_db()
        return Response(ProjectCharacterLinkSerializer(pcl).data)


class LocationRefineView(APIView):
    """
    POST /worlds/locations/<pk>/refine/  — Ort per KI verfeinern
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        pll = get_object_or_404(ProjectLocationLink, pk=pk, project__owner=request.user)

        from apps.worlds.services import refine_location_with_llm

        ok = refine_location_with_llm(pll)
        if not ok:
            return Response(
                {"detail": "KI-Verfeinerung fehlgeschlagen."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        pll.refresh_from_db()
        return Response(ProjectLocationLinkSerializer(pll).data)
