from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import IdeaImportDraft
from .serializers import IdeaImportCommitSerializer, IdeaImportDraftSerializer


class IdeaImportDraftListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = IdeaImportDraftSerializer

    def get_queryset(self):
        return IdeaImportDraft.objects.filter(project__owner=self.request.user).select_related("project")


class IdeaImportDraftDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = IdeaImportDraftSerializer

    def get_queryset(self):
        return IdeaImportDraft.objects.filter(project__owner=self.request.user)


class IdeaImportCommitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        draft = IdeaImportDraft.objects.filter(pk=pk, project__owner=request.user).first()
        if not draft:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = IdeaImportCommitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if draft.status == IdeaImportDraft.Status.COMMITTED:
            return Response(
                {"detail": "Draft bereits vollständig committed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": "Commit-Logik wird in Phase 3 implementiert.", "draft_id": str(draft.id)},
            status=status.HTTP_202_ACCEPTED,
        )


class IdeaImportDiscardView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        draft = IdeaImportDraft.objects.filter(pk=pk, project__owner=request.user).first()
        if not draft:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        draft.status = IdeaImportDraft.Status.DISCARDED
        draft.save(update_fields=["status"])
        return Response({"status": "discarded"}, status=status.HTTP_200_OK)
