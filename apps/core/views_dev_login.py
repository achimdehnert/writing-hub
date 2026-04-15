"""
Dev Auto-Login via signed token — for Playwright/automated testing.

Security: Token is signed with SECRET_KEY, expires after 5 minutes.
Same principle as password-reset links (django.core.signing).
"""
import logging

from django.contrib.auth import get_user_model, login
from django.core import signing
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.views import View

logger = logging.getLogger(__name__)

TOKEN_MAX_AGE = 300  # 5 minutes


class DevLoginView(View):
    """Validate signed token and log in the user."""

    def get(self, request):
        token = request.GET.get("token")
        if not token:
            return HttpResponseBadRequest("Missing token")

        try:
            data = signing.loads(token, max_age=TOKEN_MAX_AGE)
        except signing.BadSignature:
            return HttpResponseBadRequest("Invalid or expired token")

        User = get_user_model()
        try:
            user = User.objects.get(pk=data["uid"])
        except User.DoesNotExist:
            return HttpResponseBadRequest("User not found")

        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        logger.info("Dev auto-login for user %s", user.username)
        return redirect(data.get("next", "/projekte/"))
