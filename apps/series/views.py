from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import BookSeries
from .serializers import BookSeriesSerializer


class BookSeriesListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookSeriesSerializer

    def get_queryset(self):
        return BookSeries.objects.filter(owner=self.request.user)


class BookSeriesDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookSeriesSerializer

    def get_queryset(self):
        return BookSeries.objects.filter(owner=self.request.user)
