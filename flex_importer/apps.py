from django.apps import AppConfig


class FlexImporterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'flex_importer'
    verbose_name = 'Importador Flexible'

    def ready(self):
        from . import registry
        registry.autodiscover()
