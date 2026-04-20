"""
Projects — Template Views (UC 1.5 Projekt-Vorlagen)
"""
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from .models import BookProject, ContentTypeLookup, ProjectTemplate

logger = logging.getLogger(__name__)


class TemplateListView(LoginRequiredMixin, View):
    """GET: Verfügbare Projekt-Templates anzeigen."""

    template_name = "projects/template_list.html"

    def get(self, request):
        templates = ProjectTemplate.objects.filter(
            is_active=True,
        ).filter(
            Q(owner=request.user) | Q(owner__isnull=True)
        )
        return render(request, self.template_name, {
            "templates": templates,
        })


class TemplateApplyView(LoginRequiredMixin, View):
    """POST: Neues Projekt aus Template erstellen."""

    def post(self, request, template_pk):
        tpl = get_object_or_404(
            ProjectTemplate.objects.filter(
                is_active=True,
            ).filter(Q(owner=request.user) | Q(owner__isnull=True)),
            pk=template_pk,
        )

        ct_lookup = ContentTypeLookup.objects.filter(
            slug=tpl.content_type,
        ).first()

        project = BookProject.objects.create(
            owner=request.user,
            title=request.POST.get("title", f"Neues Projekt ({tpl.name})"),
            description=tpl.description,
            content_type=tpl.content_type,
            content_type_lookup=ct_lookup,
            genre=tpl.default_genre,
            target_audience=tpl.default_audience,
            target_word_count=tpl.default_target_words,
        )
        messages.success(request, f'Projekt aus Vorlage "{tpl.name}" erstellt.')
        return redirect("projects:detail", pk=project.pk)
