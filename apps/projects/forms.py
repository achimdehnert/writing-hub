"""
Projects — Forms (Input-Validation via Django ModelForm)
"""

from __future__ import annotations

from django import forms

from .models import PublisherProfile


class PublisherProfileForm(forms.ModelForm):
    """Form für Verlagsprofil — validiert URLs, Pflichtfelder, Choices."""

    class Meta:
        model = PublisherProfile
        fields = [
            "name",
            "imprint",
            "logo_url",
            "default_copyright_holder",
            "default_language",
            "default_bisac_category",
            "default_age_rating",
            "website",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Verlagsname"}),
            "imprint": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "z.B. Sachbuch-Reihe, Belletristik-Label"}
            ),
            "logo_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://..."}),
            "default_copyright_holder": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "z.B. Mein Verlag GmbH"}
            ),
            "default_language": forms.Select(attrs={"class": "form-select"}),
            "default_bisac_category": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "z.B. FICTION / Literary"}
            ),
            "default_age_rating": forms.Select(attrs={"class": "form-select"}),
            "website": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://mein-verlag.de"}),
        }

    LANGUAGE_CHOICES = [
        ("de", "Deutsch"),
        ("en", "Englisch"),
        ("fr", "Französisch"),
        ("es", "Spanisch"),
    ]
    AGE_RATING_CHOICES = [
        ("0", "Ab 0"),
        ("6", "Ab 6"),
        ("12", "Ab 12"),
        ("16", "Ab 16"),
        ("18", "Ab 18"),
    ]

    default_language = forms.ChoiceField(choices=LANGUAGE_CHOICES, initial="de")
    default_age_rating = forms.ChoiceField(choices=AGE_RATING_CHOICES, initial="0")
