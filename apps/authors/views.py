"""
Authors — Views für Autor-Profile und Schreibstile.
"""
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView, ListView

from .models import Author, WritingStyle, WritingStyleSample
from . import services

logger = logging.getLogger(__name__)


class AuthorListView(LoginRequiredMixin, ListView):
    template_name = "authors/author_list.html"
    context_object_name = "authors"

    def get_queryset(self):
        return Author.objects.filter(
            owner=self.request.user, is_active=True
        ).prefetch_related("writing_styles")


class AuthorCreateView(LoginRequiredMixin, View):
    template_name = "authors/author_form.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        name = request.POST.get("name", "").strip()
        if not name:
            return render(request, self.template_name, {"error": "Name ist pflicht."})
        author = Author.objects.create(
            owner=request.user,
            name=name,
            bio=request.POST.get("bio", ""),
        )
        messages.success(request, f'Autor „{author.name}“ angelegt.')
        return redirect("authors:detail", pk=author.pk)


class AuthorDetailView(LoginRequiredMixin, DetailView):
    template_name = "authors/author_detail.html"
    context_object_name = "author"

    def get_queryset(self):
        return Author.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["styles"] = self.object.writing_styles.filter(
            is_active=True
        ).prefetch_related("samples")
        return ctx


class AuthorUpdateView(LoginRequiredMixin, View):
    template_name = "authors/author_form.html"

    def get(self, request, pk):
        author = get_object_or_404(Author, pk=pk, owner=request.user)
        return render(request, self.template_name, {"author": author, "is_edit": True})

    def post(self, request, pk):
        author = get_object_or_404(Author, pk=pk, owner=request.user)
        author.name = request.POST.get("name", author.name).strip() or author.name
        author.bio = request.POST.get("bio", author.bio)
        author.save(update_fields=["name", "bio"])
        messages.success(request, f'Autor „{author.name}“ aktualisiert.')
        return redirect("authors:detail", pk=author.pk)


class WritingStyleCreateView(LoginRequiredMixin, View):
    template_name = "authors/style_form.html"

    def get(self, request, pk):
        author = get_object_or_404(Author, pk=pk, owner=request.user)
        return render(request, self.template_name, {"author": author})

    def post(self, request, pk):
        author = get_object_or_404(Author, pk=pk, owner=request.user)
        name = request.POST.get("name", "").strip()
        source_text = request.POST.get("source_text", "").strip()

        # File-Upload Support
        if not source_text and request.FILES.get("source_file"):
            f = request.FILES["source_file"]
            try:
                source_text = f.read().decode("utf-8", errors="replace")
            except Exception:
                source_text = ""

        if not name:
            return render(request, self.template_name, {
                "author": author,
                "error": "Name ist pflicht.",
                "post": request.POST,
            })

        style = WritingStyle.objects.create(
            author=author,
            name=name,
            description=request.POST.get("description", ""),
            source_text=source_text,
        )
        messages.success(request, f'Schreibstil „{style.name}“ angelegt.')

        # Direkt analysieren wenn Text vorhanden
        if source_text and request.POST.get("auto_analyze"):
            return redirect("authors:style_analyze", pk=style.pk)
        return redirect("authors:style_detail", pk=style.pk)


class WritingStyleDetailView(LoginRequiredMixin, DetailView):
    template_name = "authors/style_detail.html"
    context_object_name = "style"

    def get_queryset(self):
        return WritingStyle.objects.filter(
            author__owner=self.request.user
        ).select_related("author")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["samples"] = self.object.samples.all().order_by("situation")
        ctx["situations"] = WritingStyleSample.SITUATIONS
        return ctx


class WritingStyleUpdateView(LoginRequiredMixin, View):
    template_name = "authors/style_form.html"

    def get(self, request, pk):
        style = get_object_or_404(
            WritingStyle, pk=pk, author__owner=request.user
        )
        return render(request, self.template_name, {
            "style": style,
            "author": style.author,
            "is_edit": True,
        })

    def post(self, request, pk):
        style = get_object_or_404(
            WritingStyle, pk=pk, author__owner=request.user
        )
        style.name = request.POST.get("name", style.name).strip() or style.name
        style.description = request.POST.get("description", style.description)
        new_text = request.POST.get("source_text", "").strip()

        if not new_text and request.FILES.get("source_file"):
            f = request.FILES["source_file"]
            try:
                new_text = f.read().decode("utf-8", errors="replace")
            except Exception:
                new_text = ""

        if new_text:
            style.source_text = new_text
            style.status = WritingStyle.Status.DRAFT
            style.style_profile = ""
            style.style_prompt = ""
        style.save()
        messages.success(request, f'Schreibstil „{style.name}“ aktualisiert.')
        return redirect("authors:style_detail", pk=style.pk)


class WritingStyleAnalyzeView(LoginRequiredMixin, View):
    """Startet LLM-Analyse des Schreibstils (synchron)."""

    def post(self, request, pk):
        style = get_object_or_404(
            WritingStyle, pk=pk, author__owner=request.user
        )
        ok = services.analyze_style(style)
        if ok:
            messages.success(
                request,
                f'Stil „{style.name}“ erfolgreich analysiert. Jetzt Beispieltexte generieren.'
            )
        else:
            messages.error(
                request,
                f'Analyse fehlgeschlagen: {style.error_message}'
            )
        return redirect("authors:style_detail", pk=style.pk)

    def get(self, request, pk):
        return redirect("authors:style_detail", pk=pk)


class WritingStyleSamplesView(LoginRequiredMixin, View):
    """Generiert Beispieltexte für alle Situationen."""

    def post(self, request, pk):
        style = get_object_or_404(
            WritingStyle, pk=pk, author__owner=request.user
        )
        if style.status != WritingStyle.Status.READY:
            messages.warning(request, "Bitte zuerst den Stil analysieren.")
            return redirect("authors:style_detail", pk=style.pk)
        count = services.generate_samples(style)
        if count > 0:
            messages.success(request, f'{count} Beispieltexte generiert.')
        else:
            messages.info(request, 'Alle Beispieltexte bereits vorhanden.')
        return redirect("authors:style_detail", pk=style.pk)

    def get(self, request, pk):
        return redirect("authors:style_detail", pk=pk)


class SampleUpdateView(LoginRequiredMixin, View):
    """Einzelnen Beispieltext bearbeiten oder neu generieren."""

    def post(self, request, pk, situation):
        style = get_object_or_404(
            WritingStyle, pk=pk, author__owner=request.user
        )
        action = request.POST.get("action", "save")

        if action == "regenerate":
            style_desc = services.get_style_prompt_for_writing(style)
            situation_label = dict(WritingStyleSample.SITUATIONS).get(situation, situation)
            try:
                from apps.authoring.services.llm_router import LLMRouter
                router = LLMRouter()
                result = router.completion(
                    action_code="chapter_write",
                    messages=[
                        {"role": "system", "content": (
                            "Du bist ein professioneller Romanautor. "
                            "Schreibe kurze Beispieltexte (150-250 Wörter) in einem vorgegebenen Schreibstil. "
                            "Antworte nur mit dem Text."
                        )},
                        {"role": "user", "content": (
                            f"Schreibstil:\n{style_desc}\n\n"
                            f"Situation: {situation_label}\n"
                            f"Schreibe einen neuen Beispieltext für diese Situation. 150-250 Wörter."
                        )},
                    ],
                )
                sample, _ = WritingStyleSample.objects.update_or_create(
                    style=style, situation=situation,
                    defaults={"text": result},
                )
                messages.success(request, f'Beispieltext ({situation_label}) neu generiert.')
            except Exception as exc:
                messages.error(request, f'Fehler: {exc}')
        else:
            text = request.POST.get("text", "").strip()
            notes = request.POST.get("notes", "")
            if text:
                WritingStyleSample.objects.update_or_create(
                    style=style, situation=situation,
                    defaults={"text": text, "notes": notes},
                )
                messages.success(request, 'Beispieltext gespeichert.')

        return redirect("authors:style_detail", pk=style.pk)


class WritingStyleDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        style = get_object_or_404(
            WritingStyle, pk=pk, author__owner=request.user
        )
        author_pk = style.author.pk
        name = style.name
        style.delete()
        messages.success(request, f'Schreibstil „{name}“ gelöscht.')
        return redirect("authors:detail", pk=author_pk)
