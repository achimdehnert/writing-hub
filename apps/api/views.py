"""
API App — Service-to-Service REST-Endpunkte für bfagent → writing-hub (ADR-083)

Auth: JWT oder Shared Secret via Authorization-Header.
Phase 3: Vollständige Implementierung aller Endpunkte.
"""
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class ServiceTokenPermission:
    """
    Service-to-Service Auth via BFAGENT_API_SECRET.
    Verwendet als Permission-Klasse oder standalone Check.
    """

    @staticmethod
    def check(request) -> bool:
        secret = getattr(settings, "BFAGENT_API_SECRET", "")
        if not secret:
            return False
        auth_header = request.headers.get("Authorization", "")
        return auth_header == f"Bearer {secret}"


class WorldsApiView(APIView):
    """
    GET /api/v1/worlds/?owner=<user_id>
    Liefert Welten eines Users für bfagent-Integration.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.worlds.models import World
        from apps.worlds.serializers import WorldSerializer

        owner_id = request.query_params.get("owner")
        qs = World.objects.all()
        if owner_id:
            qs = qs.filter(owner_id=owner_id)
        else:
            qs = qs.filter(owner=request.user)

        serializer = WorldSerializer(qs, many=True)
        return Response(serializer.data)


class WorldCharactersApiView(APIView):
    """
    GET /api/v1/worlds/<id>/characters/
    Liefert Charaktere einer Welt.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, world_id):
        from apps.worlds.models import WorldCharacter
        from apps.worlds.serializers import WorldCharacterSerializer

        qs = WorldCharacter.objects.filter(
            world_id=world_id,
            world__owner=request.user,
        )
        serializer = WorldCharacterSerializer(qs, many=True)
        return Response(serializer.data)


class ProjectOutlineApiView(APIView):
    """
    GET /api/v1/projects/<id>/outline/
    Liefert den aktiven Outline-Stand eines Projekts.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        from apps.projects.models import OutlineVersion
        from apps.projects.serializers import OutlineVersionSerializer

        qs = OutlineVersion.objects.filter(
            project_id=project_id,
            project__owner=request.user,
            is_active=True,
        ).order_by("-created_at")

        serializer = OutlineVersionSerializer(qs, many=True)
        return Response(serializer.data)


class IdeaImportApiView(APIView):
    """
    POST /api/v1/idea-import/
    Erstellt einen neuen IdeaImportDraft via API (bfagent-Integration).

    Phase 3: LLM-Extraktion wird als Celery-Task ausgeführt (ADR-081 Befund 1).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.idea_import.serializers import IdeaImportDraftSerializer

        serializer = IdeaImportDraftSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            {"detail": "IdeaImport API wird in Phase 3 vollständig implementiert."},
            status=status.HTTP_202_ACCEPTED,
        )


class HealthApiView(APIView):
    """
    GET /api/v1/health/
    Service-Health-Check für bfagent-Monitoring.
    """
    permission_classes = []

    def get(self, request):
        return Response({
            "status": "ok",
            "service": "writing-hub",
            "version": "phase-3",
        })
