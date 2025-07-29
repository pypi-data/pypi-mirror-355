from django.apps import AppConfig

class HealthcheckPlusConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'healthcheck_plus'

    def ready(self):
        # Load custom checks and apply settings
        from . import settings
