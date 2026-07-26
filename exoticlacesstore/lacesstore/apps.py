from django.apps import AppConfig


class LacesstoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lacesstore'


    def ready(self):
        import lacesstore.signals  # Register the signals
