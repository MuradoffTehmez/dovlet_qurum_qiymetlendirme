# core/apps.py

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        # Siqnalları import edirik ki, Django onları tanısın
        import core.signals
        # Audit logging siqnallarını da import edirik
        import core.audit
