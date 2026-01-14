"""
Registry for FlexImporter classes
"""
import importlib
from django.apps import apps
from django.conf import settings


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
