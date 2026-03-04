from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import BookProject, OutlineVersion
from .serializers import BookProjectSerializer, OutlineVersionSerializer


class BookProjectListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookProjectSerializer

    def get_queryset(self):
        return BookProject.objects.filter(owner=self.request.user)


class BookProjectDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookProjectSerializer

    def get_queryset(self):
        return BookProject.objects.filter(owner=self.request.user)


class ProjectOutlineView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OutlineVersionSerializer

    def get_queryset(self):
        return OutlineVersion.objects.filter(
            project__pk=self.kwargs["project_pk"],
            project__owner=self.request.user,
        )
