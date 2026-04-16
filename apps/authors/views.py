"""
Authors — Views für Autor-Profile und Schreibstile (Style Lab Builder).
"""
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView, ListView

from .models import Author, GenreProfile, SituationType, WritingStyle, WritingStyleSample
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
        messages.success(request, f'Autor \u201e{author.name}\u201c angelegt.')
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
        messages.success(request, f'Autor \u201e{author.name}\u201c aktualisiert.')
        return redirect("authors:detail", pk=author.pk)


class WritingStyleCreateView(LoginRequiredMixin, View):
    template_name = "authors/style_form.html"

    def get(self, request, pk):
        author = get_object_or_404(Author, pk=pk, owner=request.user)
        genres = GenreProfile.objects.filter(is_active=True)
        return render(request, self.template_name, {"author": author, "genres": genres})

    def post(self, request, pk):
        author = get_object_or_404(Author, pk=pk, owner=request.user)
        name = request.POST.get("name", "").strip()
        source_text = request.POST.get("source_text", "").strip()

        if not source_text and request.FILES.get("source_file"):
            f = request.FILES["source_file"]
            try:
                source_text = f.read().decode("utf-8", errors="replace")
            except Exception:
                source_text = ""

        if not name:
            genres = GenreProfile.objects.filter(is_active=True)
            return render(request, self.template_name, {
                "author": author,
                "genres": genres,
                "error": "Name ist pflicht.",
                "post": request.POST,
            })

        genre_profile = None
        genre_pk = request.POST.get("genre_profile")
        if genre_pk:
            genre_profile = GenreProfile.objects.filter(pk=genre_pk, is_active=True).first()

        style = WritingStyle.objects.create(
            author=author,
            name=name,
            genre_profile=genre_profile,
            description=request.POST.get("description", ""),
            source_text=source_text,
            do_list=_parse_list_input(request.POST.get("do_list", "")),
            dont_list=_parse_list_input(request.POST.get("dont_list", "")),
            taboo_list=_parse_list_input(request.POST.get("taboo_list", "")),
            signature_moves=_parse_list_input(request.POST.get("signature_moves", "")),
        )
        messages.success(request, f'Schreibstil \u201e{style.name}\u201c angelegt.')

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
        style = self.object
        samples = style.samples.all().select_related("situation_type").order_by("situation")
        ctx["samples"] = samples

        # Genre-aware situation types (fallback to legacy list)
        if style.genre_profile:
            ctx["situation_types"] = style.genre_profile.situation_types.filter(
                is_active=True
            ).order_by("sort_order")
            ctx["situations"] = [
                (st.slug, st.label) for st in ctx["situation_types"]
            ]
        else:
            ctx["situation_types"] = None
            ctx["situations"] = WritingStyleSample.SITUATIONS

        # Build sample lookup by situation key
        sample_by_key = {}
        for s in samples:
            if s.situation_type:
                sample_by_key[s.situation_type.slug] = s
            if s.situation:
                sample_by_key[s.situation] = s

        # Pre-built list: [(key, label, sample_or_None), ...]
        situation_items = []
        for key, label in ctx["situations"]:
            situation_items.append({
                "key": key,
                "label": label,
                "sample": sample_by_key.get(key),
            })
        ctx["situation_items"] = situation_items
        ctx["genres"] = GenreProfile.objects.filter(is_active=True)
        return ctx


class WritingStyleUpdateView(LoginRequiredMixin, View):
    template_name = "authors/style_form.html"

    def get(self, request, pk):
        style = get_object_or_404(
            WritingStyle, pk=pk, author__owner=request.user
        )
        genres = GenreProfile.objects.filter(is_active=True)
        return render(request, self.template_name, {
            "style": style,
            "author": style.author,
            "is_edit": True,
            "genres": genres,
            "do_list_str": "\n".join(style.do_list or []),
            "dont_list_str": "\n".join(style.dont_list or []),
            "taboo_list_str": "\n".join(style.taboo_list or []),
            "signature_moves_str": "\n".join(style.signature_moves or []),
        })

    def post(self, request, pk):
        style = get_object_or_404(
            WritingStyle, pk=pk, author__owner=request.user
        )
        style.name = request.POST.get("name", style.name).strip() or style.name
        style.description = request.POST.get("description", style.description)
        style.do_list = _parse_list_input(request.POST.get("do_list", ""))
        style.dont_list = _parse_list_input(request.POST.get("dont_list", ""))
        style.taboo_list = _parse_list_input(request.POST.get("taboo_list", ""))
        style.signature_moves = _parse_list_input(request.POST.get("signature_moves", ""))

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

        genre_pk = request.POST.get("genre_profile")
        if genre_pk:
            style.genre_profile = GenreProfile.objects.filter(pk=genre_pk, is_active=True).first()
        elif genre_pk == "":
            style.genre_profile = None
        style.save()
        messages.success(request, f'Schreibstil \u201e{style.name}\u201c aktualisiert.')
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
                f'Stil \u201e{style.name}\u201c erfolgreich analysiert.'
            )
        else:
            messages.error(
                request,
                f'Analyse fehlgeschlagen: {style.error_message}'
            )
        return redirect("authors:style_detail", pk=style.pk)

    def get(self, request, pk):
        return redirect("authors:style_detail", pk=pk)


class WritingStyleExtractRulesView(LoginRequiredMixin, View):
    """Extrahiert DO/DONT/Taboo-Regeln aus dem Quelltext per LLM."""

    def post(self, request, pk):
        style = get_object_or_404(
            WritingStyle, pk=pk, author__owner=request.user
        )
        ok, result = services.extract_style_rules(style)
        if ok:
            return JsonResponse({
                "ok": True,
                "do_list": result.get("do_list", []),
                "dont_list": result.get("dont_list", []),
                "taboo_list": result.get("taboo_list", []),
                "signature_moves": result.get("signature_moves", []),
            })
        return JsonResponse({"ok": False, "error": result.get("error", "Unbekannter Fehler")})

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

        # Resolve SituationType and label from genre or legacy
        situation_type = None
        situation_label = situation
        llm_hint = ""
        if style.genre_profile:
            st = SituationType.objects.filter(
                genre_profile=style.genre_profile, slug=situation
            ).first()
            if st:
                situation_type = st
                situation_label = st.label
                llm_hint = st.llm_prompt_hint or ""
        else:
            situation_label = dict(WritingStyleSample.SITUATIONS).get(situation, situation)

        if action == "regenerate":
            style_desc = services.get_style_prompt_for_writing(style)
            try:
                from apps.authoring.services.llm_router import LLMRouter
                from apps.core.prompt_utils import render_prompt
                router = LLMRouter()
                prompt_msgs = render_prompt(
                    "authors/generate_sample",
                    style_desc=style_desc,
                    situation_label=situation_label,
                    llm_prompt_hint=llm_hint,
                )
                result = router.completion(
                    action_code="chapter_write",
                    messages=prompt_msgs,
                )
                WritingStyleSample.objects.update_or_create(
                    style=style, situation=situation,
                    defaults={"text": result, "situation_type": situation_type},
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
                    defaults={"text": text, "notes": notes, "situation_type": situation_type},
                )
                messages.success(request, 'Beispieltext gespeichert.')

        return redirect("authors:style_detail", pk=style.pk)


class WritingStyleImportView(LoginRequiredMixin, View):
    """Importiert einen Schreibstil aus einer Markdown-Datei."""
    template_name = "authors/style_import.html"

    def get(self, request, pk):
        author = get_object_or_404(Author, pk=pk, owner=request.user)
        return render(request, self.template_name, {"author": author})

    def post(self, request, pk):
        from .services_import import import_style_from_markdown, parse_style_markdown

        author = get_object_or_404(Author, pk=pk, owner=request.user)

        markdown_text = ""
        if request.FILES.get("md_file"):
            f = request.FILES["md_file"]
            try:
                markdown_text = f.read().decode("utf-8", errors="replace")
            except Exception:
                markdown_text = ""
        if not markdown_text:
            markdown_text = request.POST.get("md_text", "").strip()

        if not markdown_text:
            return render(request, self.template_name, {
                "author": author,
                "error": "Bitte eine Markdown-Datei hochladen oder Text eingeben.",
            })

        name_override = request.POST.get("name", "").strip()

        # Preview mode: parse and show results before creating
        if request.POST.get("action") == "preview":
            parsed = parse_style_markdown(markdown_text)
            return render(request, self.template_name, {
                "author": author,
                "preview": parsed,
                "md_text": markdown_text,
                "name_override": name_override,
            })

        # Import mode: create WritingStyle
        auto_analyze = bool(request.POST.get("auto_analyze"))
        style, parsed = import_style_from_markdown(
            author,
            markdown_text,
            name_override=name_override,
            auto_analyze=auto_analyze,
        )

        if auto_analyze and not parsed.has_structured_data:
            messages.info(
                request,
                f'Stil \u201e{style.name}\u201c importiert (wenig Struktur erkannt). '
                'Starte LLM-Analyse...'
            )
            return redirect("authors:style_analyze", pk=style.pk)

        messages.success(
            request,
            f'Stil \u201e{style.name}\u201c importiert '
            f'({len(parsed.sections_found)} Sektionen erkannt).'
        )
        return redirect("authors:style_detail", pk=style.pk)


class WritingStyleDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        style = get_object_or_404(
            WritingStyle, pk=pk, author__owner=request.user
        )
        author_pk = style.author.pk
        name = style.name
        style.delete()
        messages.success(request, f'Schreibstil \u201e{name}\u201c gelöscht.')
        return redirect("authors:detail", pk=author_pk)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_list_input(raw: str) -> list[str]:
    """Parses newline or comma-separated list input into a clean list."""
    if not raw:
        return []
    items = [line.strip().lstrip("-\u2022\u25e6").strip() for line in raw.splitlines()]
    items = [i for i in items if i]
    if not items:
        items = [i.strip() for i in raw.split(",") if i.strip()]
    return items
