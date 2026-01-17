"""
Management command to sync importer permissions
"""
from django.core.management.base import BaseCommand
from flex_importer.registry import importer_registry


class Command(BaseCommand):
    help = 'Sincroniza permisos de importadores con clases registradas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué se actualizaría sin hacer cambios',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('Modo DRY-RUN: No se harán cambios\n'))

        self.stdout.write(self.style.SUCCESS('=== Sincronizando permisos de importadores ===\n'))

        # List all registered importers
        importers = importer_registry.get_all_importers()
        self.stdout.write(f'Importadores registrados: {len(importers)}\n')

        for class_name, importer_class in importers.items():
            codename = importer_registry.get_permission_codename(importer_class)
            name = importer_registry.get_permission_name(importer_class)
            self.stdout.write(f'  - {importer_class.get_verbose_name()}: {codename}')

        self.stdout.write('\n' + '=' * 50 + '\n')

        if not dry_run:
            # Sync permissions
            created, deleted = importer_registry.sync_permissions()

            self.stdout.write(
                self.style.SUCCESS(
                    f'Permisos creados: {created}'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Permisos eliminados: {deleted}'
                )
            )

            if created > 0 or deleted > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        '\n¡Sincronización completada exitosamente!'
                    )
                )
            else:
                self.stdout.write('\nNo se requirieron cambios.')
        else:
            self.stdout.write(
                '\nEjecuta sin --dry-run para aplicar los cambios'
            )
