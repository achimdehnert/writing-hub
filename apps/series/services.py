"""Series query helpers (ADR-041)."""

from __future__ import annotations


def get_genre_lookups():
    """Return all GenreLookup options ordered for form display."""
    from apps.projects.models import GenreLookup

    return GenreLookup.objects.all().order_by("order", "name")
