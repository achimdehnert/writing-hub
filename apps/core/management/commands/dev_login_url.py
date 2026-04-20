"""
Generate a signed auto-login URL for Playwright/automated testing.

Usage:
    python manage.py dev_login_url
    python manage.py dev_login_url --next /projekte/new/
"""

from django.contrib.auth import get_user_model
from django.core import signing
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a signed auto-login URL (expires in 5 minutes)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--next",
            default="/projekte/",
            help="Redirect target after login (default: /projekte/)",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        user = User.objects.filter(is_superuser=True).first() or User.objects.first()
        if not user:
            self.stderr.write("No users found")
            return

        token = signing.dumps({"uid": str(user.pk), "next": options["next"]})
        self.stdout.write(f"/dev-login/?token={token}")
