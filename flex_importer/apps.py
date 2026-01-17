from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.dispatch import receiver


class FlexImporterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'flex_importer'
    verbose_name = 'Importador Flexible'

    def ready(self):
        from . import registry
        registry.autodiscover()
        # Register post_migrate signal
        post_migrate.connect(sync_importer_permissions, sender=self)


def sync_importer_permissions(sender, **kwargs):
    """
    Signal handler to sync importer permissions after migrations.

    This ensures that permissions are automatically created/updated/deleted
    whenever migrations run, keeping them in sync with registered importers.
    """
    from .registry import importer_registry

    # Only sync if tables exist (avoid errors during initial migration)
    try:
        created, deleted = importer_registry.sync_permissions()
        if created > 0 or deleted > 0:
            print(f"Synced importer permissions: {created} created, {deleted} deleted")
    except Exception:
        # Silently fail during initial migrations when tables don't exist yet
        pass
