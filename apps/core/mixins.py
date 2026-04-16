"""
ComputedFieldsMixin — Auto-sync derived fields in save(update_fields=...).

Problem: Django's save(update_fields=[...]) skips fields not in the list,
even if the model's save() override computes them. This silently drops
computed values.

Solution: Declare COMPUTED_FIELDS mapping, and the mixin auto-extends
update_fields when a dependency is present.

Usage:
    class OutlineNode(ComputedFieldsMixin):
        COMPUTED_FIELDS = {
            "word_count": (["content"], "_compute_word_count"),
        }

        def _compute_word_count(self):
            self.word_count = len(self.content.split()) if self.content else 0
"""

from __future__ import annotations

from typing import ClassVar

from django.db import models


class ComputedFieldsMixin(models.Model):
    """Auto-include computed fields in save(update_fields=...).

    Subclasses declare COMPUTED_FIELDS:
        {field_name: ([dependency_fields], "compute_method_name")}

    When save(update_fields=["content", ...]) is called and "content"
    is a dependency of "word_count", the mixin:
      1. Calls _compute_word_count()
      2. Appends "word_count" to update_fields

    On full save (no update_fields), all computed fields are refreshed.
    """

    COMPUTED_FIELDS: ClassVar[dict[str, tuple[list[str], str]]] = {}

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            update_fields = list(update_fields)
            for computed, (deps, method) in self.COMPUTED_FIELDS.items():
                if any(d in update_fields for d in deps):
                    getattr(self, method)()
                    if computed not in update_fields:
                        update_fields.append(computed)
            kwargs["update_fields"] = update_fields
        else:
            for _computed, (_deps, method) in self.COMPUTED_FIELDS.items():
                getattr(self, method)()
        super().save(*args, **kwargs)
