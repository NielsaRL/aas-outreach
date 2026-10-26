from django.apps import AppConfig


class OutreachConfig(AppConfig):
    name = "outreach"

    def ready(self):
        from . import signals  # noqa: F401