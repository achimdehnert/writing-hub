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
        outlines = OutlineVersion.objects.filter(project=self.object).order_by("-created_at")
        ctx["outlines"] = outlines
        selected_id = self.request.GET.get("outline")
        if selected_id:
            try:
                selected = outlines.get(pk=selected_id)
            except OutlineVersion.DoesNotExist:
                selected = outlines.filter(is_active=True).first() or outlines.first()
        else:
            selected = outlines.filter(is_active=True).first() or outlines.first()
        ctx["selected_outline"] = selected
        ctx["outline_nodes"] = selected.nodes.order_by("order") if selected else []
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
        from apps.projects.models import OutlineNode
        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        name = request.POST.get("name", "").strip() or "Erster Entwurf"
        notes = request.POST.get("notes", "")
        chapter_count = int(request.POST.get("chapter_count", 0) or 0)
        version = OutlineVersion.objects.create(
            project=project,
            created_by=request.user,
            name=name,
            source="manual",
            notes=notes,
            is_active=True,
        )
        if chapter_count > 0:
            OutlineNode.objects.bulk_create([
                OutlineNode(
                    outline_version=version,
                    title=f"Kapitel {i + 1}",
                    beat_type="chapter",
                    order=i + 1,
                )
                for i in range(min(chapter_count, 50))
            ])
        return redirect("projects:detail", pk=pk)


class OutlineGenerateView(LoginRequiredMixin, View):
    """Django POST view (kein DRF) — kein CSRF-Problem bei session auth."""
    def post(self, request, pk):
        from apps.authoring.services.outline_service import OutlineGeneratorService
        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        framework = request.POST.get("framework", "three_act")
        chapter_count = int(request.POST.get("chapter_count", 12) or 12)
        svc = OutlineGeneratorService()
        result = svc.generate_outline(
            project_id=str(project.pk),
            framework=framework,
            chapter_count=chapter_count,
        )
        if result.success and result.nodes:
            svc.save_outline(
                project_id=str(project.pk),
                nodes=result.nodes,
                name=f"KI: {framework.replace('_', ' ').title()} ({chapter_count} Kap.)",
                user=request.user,
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
