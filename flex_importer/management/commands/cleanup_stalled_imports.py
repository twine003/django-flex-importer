"""
Management command to detect and cleanup stalled import jobs.

This command checks for import jobs that are stuck in 'pending' or 'processing'
status for too long and marks them as failed.

Usage:
    python manage.py cleanup_stalled_imports
    python manage.py cleanup_stalled_imports --timeout 15  # Custom timeout in minutes
    python manage.py cleanup_stalled_imports --dry-run     # See what would be cleaned without actually doing it
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from flex_importer.models import ImportJob


class Command(BaseCommand):
    help = 'Detect and cleanup stalled import jobs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout',
            type=int,
            default=10,
            help='Timeout in minutes before considering a job stalled (default: 10)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned without actually doing it'
        )

    def handle(self, *args, **options):
        timeout_minutes = options['timeout']
        dry_run = options['dry_run']

        self.stdout.write("="*70)
        self.stdout.write(self.style.WARNING(
            f"LIMPIEZA DE IMPORTACIONES ESTANCADAS (timeout: {timeout_minutes} min)"
        ))
        self.stdout.write("="*70)
        self.stdout.write()

        # Find stalled jobs
        stalled_jobs = []
        for job in ImportJob.objects.filter(status__in=['pending', 'processing']):
            if job.is_stalled(timeout_minutes):
                stalled_jobs.append(job)

        if not stalled_jobs:
            self.stdout.write(self.style.SUCCESS(
                "[OK] No se encontraron importaciones estancadas"
            ))
            return

        self.stdout.write(self.style.WARNING(
            f"[!] Se encontraron {len(stalled_jobs)} importaciones estancadas:\n"
        ))

        # Display stalled jobs
        for job in stalled_jobs:
            time_elapsed = timezone.now() - job.created_at
            hours, remainder = divmod(time_elapsed.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            self.stdout.write(f"  • ID {job.id}: {job.importer_name}")
            self.stdout.write(f"    Estado: {job.status}")
            self.stdout.write(f"    Creado: {job.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            self.stdout.write(f"    Tiempo transcurrido: {hours}h {minutes}m {seconds}s")
            self.stdout.write()

        if dry_run:
            self.stdout.write(self.style.WARNING(
                "\n[DRY RUN] No se realizaran cambios (usa sin --dry-run para aplicar)\n"
            ))
            return

        # Mark as failed
        self.stdout.write(self.style.WARNING(
            "Marcando trabajos como fallidos...\n"
        ))

        marked_count = 0
        for job in stalled_jobs:
            if job.mark_as_failed_if_stalled(timeout_minutes):
                marked_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f"  [OK] Job ID {job.id} marcado como fallido"
                ))

        self.stdout.write()
        self.stdout.write("="*70)
        self.stdout.write(self.style.SUCCESS(
            f"[OK] Completado: {marked_count} trabajos marcados como fallidos"
        ))
        self.stdout.write("="*70)
