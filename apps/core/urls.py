from django.http import JsonResponse
from django.urls import path

app_name = "core"


def health_check(request):
    return JsonResponse({"status": "ok", "service": "writing-hub"})


urlpatterns = [
    path("", health_check, name="health"),
]
