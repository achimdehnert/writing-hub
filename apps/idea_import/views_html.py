"""
Idea Import — HTML Frontend Views
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from .models import IdeaImportDraft


class IdeaListView(LoginRequiredMixin, ListView):
    model = IdeaImportDraft
    template_name = "ideas/idea_list.html"
    context_object_name = "drafts"
    paginate_by = 20

    def get_queryset(self):
        return (
            IdeaImportDraft.objects
            .filter(project__owner=self.request.user)
            .exclude(status=IdeaImportDraft.Status.DISCARDED)
            .select_related("project")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        ctx["total"] = qs.count()
        ctx["pending"] = qs.filter(status=IdeaImportDraft.Status.PENDING_REVIEW).count()
        ctx["committed"] = qs.filter(status=IdeaImportDraft.Status.COMMITTED).count()
        return ctx
