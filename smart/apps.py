from django.apps import AppConfig


class SmartConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'smart'
    
    def ready(self):
        import smart.signals
