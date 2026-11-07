from django.apps import AppConfig


class TranscriptionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transcriptions'
    verbose_name = 'Транскрипции'

    def ready(self):
        import transcriptions.signals  # noqa: F401
