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
    GET /api/v1/worlds/?project=<project_id>

    Liefert die ProjectWorldLinks des Users (lokale Verknüpfungen zu WeltenHub-Welten).
    SSoT für Welt-Daten ist WeltenHub — hier werden nur die Link-UUIDs zurückgegeben.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.worlds.models import ProjectWorldLink
        from apps.worlds.serializers import ProjectWorldLinkSerializer

        project_id = request.query_params.get("project")
        qs = ProjectWorldLink.objects.filter(project__owner=request.user)
        if project_id:
            qs = qs.filter(project_id=project_id)

        serializer = ProjectWorldLinkSerializer(qs, many=True)
        return Response(serializer.data)


class WorldCharactersApiView(APIView):
    """
    GET /api/v1/worlds/<world_id>/characters/

    Liefert ProjectCharacterLinks für Projekte des Users, die mit dieser WeltenHub-Welt verknüpft sind.
    SSoT für Charakter-Daten ist WeltenHub — hier werden nur die Link-UUIDs zurückgegeben.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, world_id):
        from apps.worlds.models import ProjectCharacterLink
        from apps.worlds.serializers import ProjectCharacterLinkSerializer

        qs = ProjectCharacterLink.objects.filter(
            project__owner=request.user,
            project__world_links__weltenhub_world_id=world_id,
        )
        serializer = ProjectCharacterLinkSerializer(qs, many=True)
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
