"""
Management Command: seed_quality_gate_decisions

Legt GateDecisionType-Lookup-Einträge an (approve, review, revise, reject).
Idempotent — kann beliebig oft ausgeführt werden.

Ausführen nach erster Migration:
    python manage.py seed_quality_gate_decisions
"""

from django.core.management.base import BaseCommand


GATE_DECISIONS = [
    {
        "code": "approve",
        "name_de": "Genehmigt",
        "name_en": "Approved",
        "description": "Kapitel ist bereit für den nächsten Schritt.",
        "color": "success",
        "icon": "bi-check-circle",
        "allows_commit": True,
        "sort_order": 1,
    },
    {
        "code": "review",
        "name_de": "Review erforderlich",
        "name_en": "Needs Review",
        "description": "Manuelles Review durch Autor notwendig.",
        "color": "warning",
        "icon": "bi-eye",
        "allows_commit": False,
        "sort_order": 2,
    },
    {
        "code": "revise",
        "name_de": "Überarbeitung notwendig",
        "name_en": "Needs Revision",
        "description": "Kapitel muss überarbeitet werden.",
        "color": "danger",
        "icon": "bi-pencil",
        "allows_commit": False,
        "sort_order": 3,
    },
    {
        "code": "reject",
        "name_de": "Abgelehnt",
        "name_en": "Rejected",
        "description": "Kapitel entspricht nicht den Mindestanforderungen.",
        "color": "danger",
        "icon": "bi-x-circle",
        "allows_commit": False,
        "sort_order": 4,
    },
]


class Command(BaseCommand):
    help = "Seed GateDecisionType Lookup-Daten (idempotent)"

    def handle(self, *args, **options):
        from apps.authoring.models import GateDecisionType

        created_count = 0
        updated_count = 0

        for data in GATE_DECISIONS:
            code = data.pop("code")
            obj, created = GateDecisionType.objects.update_or_create(
                code=code,
                defaults=data,
            )
            data["code"] = code
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✅ Erstellt: {code}"))
            else:
                updated_count += 1
                self.stdout.write(f"  ↩️  Aktualisiert: {code}")

        self.stdout.write(self.style.SUCCESS(f"\nFertig: {created_count} erstellt, {updated_count} aktualisiert."))
