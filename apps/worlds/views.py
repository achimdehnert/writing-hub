"""
Worlds API Views — writing-hub

Welten und Charaktere werden ausschliesslich ueber iil-weltenfw (WeltenHub REST Client) verwaltet.
Lokal werden nur ProjectWorldLink und ProjectCharacterLink als Referenzen gespeichert.
"""

import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class WorldListView(APIView):
    """
    GET  /worlds/                  — Alle Welten des Projekts aus WeltenHub
    POST /worlds/generate/         — Neue Welt per LLM generieren + in WeltenHub speichern
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        project_id = request.query_params.get("project_id")
        if not project_id:
            return Response({"detail": "project_id erforderlich."}, status=status.HTTP_400_BAD_REQUEST)

        from apps.worlds.services import WorldBuilderService
        svc = WorldBuilderService()
        worlds = svc.get_project_worlds(project_id)
        return Response([
            {
                "id": str(w.id),
                "name": w.name,
                "description": w.description or "",
                "is_public": getattr(w, "is_public", False),
            }
            for w in worlds
        ])

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

        world_id = svc.save_to_weltenhub(result)
        if world_id:
            svc.link_to_project(project_id, world_id)

        return Response({
            "name": result.name,
            "description": result.description,
            "weltenhub_world_id": str(world_id) if world_id else None,
        }, status=status.HTTP_201_CREATED)


class WorldDetailView(APIView):
    """
    GET   /worlds/<world_id>/        — Welt-Details aus WeltenHub
    PATCH /worlds/<world_id>/expand/ — Welt-Aspekt per LLM vertiefen
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, world_id):
        try:
            from weltenfw.django import get_client
            world = get_client().worlds.get(world_id)
            return Response({
                "id": str(world.id),
                "name": world.name,
                "description": world.description or "",
                "geography": getattr(world, "geography", "") or "",
                "magic_system": getattr(world, "magic_system", "") or "",
                "history": getattr(world, "history", "") or "",
            })
        except Exception as exc:
            logger.error("WorldDetailView.get: %s", exc)
            return Response({"detail": "Welt nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)


class WorldCharacterListView(APIView):
    """
    GET  /worlds/<world_id>/characters/        — Alle Charaktere der Welt aus WeltenHub
    POST /worlds/<world_id>/characters/generate/ — Charaktere per LLM generieren
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, world_id):
        project_id = request.query_params.get("project_id")
        if project_id:
            from apps.worlds.services import WorldCharacterService
            chars = WorldCharacterService().get_project_characters(project_id)
        else:
            try:
                from weltenfw.django import get_client
                chars = list(get_client().characters.iter_all())
            except Exception as exc:
                logger.error("WorldCharacterListView.get: %s", exc)
                return Response([], status=status.HTTP_200_OK)

        return Response([
            {
                "id": str(c.id),
                "name": c.name,
                "personality": getattr(c, "personality", "") or "",
                "is_protagonist": getattr(c, "is_protagonist", False),
            }
            for c in chars
        ])

    def post(self, request, world_id):
        project_id = request.data.get("project_id")
        count = int(request.data.get("count", 5))

        from apps.worlds.services import WorldCharacterService
        svc = WorldCharacterService()
        result = svc.generate_cast(
            weltenhub_world_id=world_id,
            project_id=project_id or "",
            count=count,
            requirements=request.data.get("requirements", ""),
        )
        if not result.success:
            return Response({"detail": result.error}, status=status.HTTP_502_BAD_GATEWAY)

        saved_ids = svc.save_to_weltenhub(world_id, result.characters)
        if project_id and saved_ids:
            svc.link_to_project(project_id, saved_ids)

        return Response({
            "generated": len(result.characters),
            "saved_ids": [str(i) for i in saved_ids],
            "characters": result.characters,
        }, status=status.HTTP_201_CREATED)
