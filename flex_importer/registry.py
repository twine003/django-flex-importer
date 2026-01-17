"""
Registry for FlexImporter classes
"""
import importlib
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


class ImporterRegistry:
    """Registry to keep track of all FlexImporter classes"""

    def __init__(self):
        self._registry = {}

    def register(self, importer_class):
        """Register an importer class"""
        class_name = f"{importer_class.__module__}.{importer_class.__name__}"
        self._registry[class_name] = importer_class

    def get_all_importers(self):
        """Get all registered importers"""
        return self._registry

    def get_importer(self, class_name):
        """Get a specific importer by class name"""
        return self._registry.get(class_name)

    def get_importer_choices(self):
        """Get choices for Django select field"""
        choices = []
        for class_name, importer_class in self._registry.items():
            verbose_name = importer_class.get_verbose_name()
            choices.append((class_name, verbose_name))
        return sorted(choices, key=lambda x: x[1])

    def get_permission_codename(self, importer_class):
        """
        Get permission codename for an importer class.

        Args:
            importer_class: The importer class

        Returns:
            str: Permission codename (e.g., 'can_use_salesimporter')
        """
        class_name = importer_class.__name__.lower()
        return f'can_use_{class_name}'

    def get_permission_name(self, importer_class):
        """
        Get human-readable permission name for an importer class.

        Args:
            importer_class: The importer class

        Returns:
            str: Permission name (e.g., 'Can use Sales Importer')
        """
        verbose_name = importer_class.get_verbose_name()
        return f'Can use {verbose_name}'

    def sync_permissions(self):
        """
        Sync permissions with registered importers.

        Creates permissions for new importers and deletes permissions
        for importers that no longer exist.

        Returns:
            tuple: (created_count, deleted_count)
        """
        from .models import ImporterPermission

        # Get content type for ImporterPermission
        content_type = ContentType.objects.get_for_model(ImporterPermission)

        # Get all existing importer permissions
        existing_permissions = Permission.objects.filter(
            content_type=content_type,
            codename__startswith='can_use_'
        )

        # Track expected permission codenames
        expected_codenames = set()
        created_count = 0

        # Create permissions for all registered importers
        for class_name, importer_class in self._registry.items():
            codename = self.get_permission_codename(importer_class)
            name = self.get_permission_name(importer_class)
            expected_codenames.add(codename)

            # Create permission if it doesn't exist
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={'name': name}
            )

            # Update name if it changed
            if not created and permission.name != name:
                permission.name = name
                permission.save(update_fields=['name'])

            if created:
                created_count += 1

        # Delete permissions for importers that no longer exist
        deleted_count = 0
        for permission in existing_permissions:
            if permission.codename not in expected_codenames:
                permission.delete()
                deleted_count += 1

        return created_count, deleted_count


importer_registry = ImporterRegistry()


def autodiscover():
    """
    Auto-discover importer modules in installed apps.
    Looks for 'importers.py' in each app.
    """
    for app_config in apps.get_app_configs():
        try:
            module_name = f"{app_config.name}.importers"
            importlib.import_module(module_name)
        except ImportError:
            pass
