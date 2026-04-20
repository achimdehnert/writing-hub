"""
Publisher Profile — Verlagsprofil verwalten (UC 6.9)

Solo-Verleger: Ein Profil anlegen, das bei jedem neuen Buch als Default
für PublishingProfile (Verlagsname, Copyright, Sprache, BISAC) dient.
"""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View

from .forms import PublisherProfileForm
from .models import PublisherProfile


class PublisherProfileView(LoginRequiredMixin, View):
    """GET: Profil anzeigen/bearbeiten — POST: Profil speichern."""

    template_name = "projects/publisher_profile.html"

    def _get_profile(self, user):
        return PublisherProfile.objects.filter(owner=user, is_default=True).first()

    def get(self, request):
        profile = self._get_profile(request.user)
        form = PublisherProfileForm(instance=profile)
        return render(request, self.template_name, {"profile": profile, "form": form})

    def post(self, request):
        profile = self._get_profile(request.user)
        if not profile:
            profile = PublisherProfile(owner=request.user, is_default=True)

        form = PublisherProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Verlagsprofil gespeichert.")
            return redirect("projects:publisher_profile")

        return render(request, self.template_name, {"profile": profile, "form": form})
