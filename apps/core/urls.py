from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import path

app_name = "core"


def health_check(request):
    return JsonResponse({"status": "ok", "service": "writing-hub"})


def root_redirect(request):
    return redirect("projects:list")


urlpatterns = [
    path("", root_redirect, name="root"),
    path("health/", health_check, name="health"),
    path("healthz/", health_check, name="healthz"),
]
