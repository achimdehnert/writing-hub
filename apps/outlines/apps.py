from django.apps import AppConfig


class OutlinesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.outlines"
    verbose_name = "Outlines"

    def ready(self):
        from apps.outlines.retrievers import register_all
        register_all()
