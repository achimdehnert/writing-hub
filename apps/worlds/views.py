from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import World, WorldCharacter
from .serializers import WorldCharacterSerializer, WorldSerializer


class WorldListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WorldSerializer

    def get_queryset(self):
        return World.objects.filter(owner=self.request.user)


class WorldDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WorldSerializer

    def get_queryset(self):
        return World.objects.filter(owner=self.request.user)


class WorldCharacterListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WorldCharacterSerializer

    def get_queryset(self):
        return WorldCharacter.objects.filter(
            world__pk=self.kwargs["world_pk"],
            world__owner=self.request.user,
        )
