"""
Projects — HTML Frontend Views (ADR-083)
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .models import BookProject, OutlineVersion


class ProjectListView(LoginRequiredMixin, ListView):
    model = BookProject
    template_name = "projects/project_list.html"
    context_object_name = "projects"

    def get_queryset(self):
        return BookProject.objects.filter(owner=self.request.user, is_active=True)


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = BookProject
    template_name = "projects/project_form.html"
    fields = ["title", "description", "content_type", "genre", "target_audience", "target_word_count"]
    success_url = reverse_lazy("projects:list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = BookProject
    template_name = "projects/project_detail.html"
    context_object_name = "project"

    def get_queryset(self):
        return BookProject.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["outlines"] = OutlineVersion.objects.filter(project=self.object)
        return ctx


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = BookProject
    template_name = "projects/project_form.html"
    fields = ["title", "description", "content_type", "genre", "target_audience", "target_word_count"]

    def get_queryset(self):
        return BookProject.objects.filter(owner=self.request.user)

    def get_success_url(self):
        return reverse_lazy("projects:detail", kwargs={"pk": self.object.pk})


class OutlineCreateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        name = request.POST.get("name", "").strip() or "Erster Entwurf"
        notes = request.POST.get("notes", "")
        OutlineVersion.objects.create(
            project=project,
            created_by=request.user,
            name=name,
            source="manual",
            notes=notes,
        )
        return redirect("projects:detail", pk=pk)


class ChapterWriterView(LoginRequiredMixin, DetailView):
    model = BookProject
    template_name = "authoring/chapter_writer.html"
    context_object_name = "project"

    def get_queryset(self):
        return BookProject.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["chapters"] = []
        ctx["chapter_count"] = 0
        ctx["characters"] = []
        return ctx
