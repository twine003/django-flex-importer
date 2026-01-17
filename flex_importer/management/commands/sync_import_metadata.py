"""
Management command to sync import job metadata with importer classes
"""
from django.core.management.base import BaseCommand
from flex_importer.models import ImportJob
from flex_importer.registry import importer_registry


class Command(BaseCommand):
    help = 'Sincroniza los metadatos de las importaciones con las clases de importadores'

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

        jobs = ImportJob.objects.all()
        updated_count = 0
        not_found_count = 0

        self.stdout.write(self.style.SUCCESS('=== Sincronizando metadatos de importaciones ===\n'))

        for job in jobs:
            importer_class = importer_registry.get_importer(job.importer_class)

            if not importer_class:
                self.stdout.write(
                    self.style.ERROR(
                        f'ID {job.id} - Clase no encontrada: {job.importer_class}'
                    )
                )
                not_found_count += 1
                continue

            # Obtener valores actuales de la clase
            can_rerun_class = importer_class.can_re_run()
            verbose_name_class = importer_class.get_verbose_name()

            # Verificar si necesita actualización
            needs_update = False
            changes = []

            if job.can_re_run != can_rerun_class:
                changes.append(f'can_re_run: {job.can_re_run} -> {can_rerun_class}')
                needs_update = True

            if job.importer_name != verbose_name_class:
                changes.append(f'nombre: {job.importer_name} -> {verbose_name_class}')
                needs_update = True

            if needs_update:
                self.stdout.write(
                    self.style.WARNING(
                        f'ID {job.id} - {job.importer_name}'
                    )
                )
                for change in changes:
                    self.stdout.write(f'  * {change}')

                if not dry_run:
                    job.can_re_run = can_rerun_class
                    job.importer_name = verbose_name_class
                    job.save(update_fields=['can_re_run', 'importer_name'])
                    updated_count += 1
            else:
                self.stdout.write(
                    f'ID {job.id} - {job.importer_name}: OK'
                )

        self.stdout.write('\n' + '=' * 50)

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\nSe actualizarían {updated_count} registro(s)'
                )
            )
            self.stdout.write(
                '\nEjecuta sin --dry-run para aplicar los cambios'
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n{updated_count} registro(s) actualizado(s)'
                )
            )

        if not_found_count > 0:
            self.stdout.write(
                self.style.ERROR(
                    f'{not_found_count} importador(es) no encontrado(s)'
                )
            )
