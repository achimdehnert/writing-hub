from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.projects.models import GenreLookup
from .models import BookSeries
from .serializers import BookSeriesSerializer


# ── REST API Views ──────────────────────────────────────────────────────

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


# ── HTML Frontend Views ─────────────────────────────────────────────────

class SeriesListView(LoginRequiredMixin, ListView):
    model = BookSeries
    template_name = "series/series_list.html"
    context_object_name = "series_list"

    def get_queryset(self):
        return (
            BookSeries.objects.filter(owner=self.request.user)
            .prefetch_related("projects")
        )


class SeriesCreateView(LoginRequiredMixin, CreateView):
    model = BookSeries
    template_name = "series/series_form.html"
    fields = ["title", "description", "genre"]
    success_url = reverse_lazy("series_html:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["genre_options"] = GenreLookup.objects.all().order_by("order", "name")
        return ctx

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(
            self.request,
            f'Serie "{form.instance.title}" wurde angelegt.',
        )
        return super().form_valid(form)


class SeriesUpdateView(LoginRequiredMixin, UpdateView):
    model = BookSeries
    template_name = "series/series_form.html"
    fields = ["title", "description", "genre"]
    success_url = reverse_lazy("series_html:list")

    def get_queryset(self):
        return BookSeries.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["genre_options"] = GenreLookup.objects.all().order_by("order", "name")
        return ctx

    def form_valid(self, form):
        messages.success(
            self.request,
            f'Serie "{form.instance.title}" wurde gespeichert.',
        )
        return super().form_valid(form)


class SeriesDeleteView(LoginRequiredMixin, DeleteView):
    model = BookSeries
    template_name = "series/series_confirm_delete.html"
    success_url = reverse_lazy("series_html:list")

    def get_queryset(self):
        return BookSeries.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Serie wurde gelöscht.")
        return super().form_valid(form)
