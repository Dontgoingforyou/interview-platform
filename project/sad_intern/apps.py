from django.apps import AppConfig


class SadInternConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sad_intern'

    def ready(self):
        """Подключаем сигналы при запуске приложения."""
        import sad_intern.signals  # noqa
