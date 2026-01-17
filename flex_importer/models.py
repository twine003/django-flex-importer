"""
Models for FlexImporter
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class ImportJob(models.Model):
    """Record of import job executions"""

    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('success', 'Exitoso'),
        ('partial', 'Parcial'),
        ('failed', 'Fallido'),
    ]

    FORMAT_CHOICES = [
        ('xlsx', 'Excel (XLSX)'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
    ]

    importer_class = models.CharField(
        max_length=255,
        verbose_name='Clase Importadora'
    )
    importer_name = models.CharField(
        max_length=255,
        verbose_name='Nombre del Importador'
    )
    file_format = models.CharField(
        max_length=10,
        choices=FORMAT_CHOICES,
        verbose_name='Formato'
    )
    uploaded_file = models.FileField(
        upload_to='imports/%Y/%m/%d/',
        verbose_name='Archivo'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Estado'
    )
    total_rows = models.IntegerField(
        default=0,
        verbose_name='Total de Filas'
    )
    processed_rows = models.IntegerField(
        default=0,
        verbose_name='Filas Procesadas'
    )
    success_rows = models.IntegerField(
        default=0,
        verbose_name='Filas Exitosas'
    )
    updated_rows = models.IntegerField(
        default=0,
        verbose_name='Filas Actualizadas'
    )
    created_rows = models.IntegerField(
        default=0,
        verbose_name='Filas Creadas'
    )
    error_rows = models.IntegerField(
        default=0,
        verbose_name='Filas con Error'
    )
    error_details = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Detalles de Errores'
    )
    progress_log = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Log de Progreso'
    )
    result_message = models.TextField(
        blank=True,
        verbose_name='Mensaje de Resultado'
    )
    can_re_run = models.BooleanField(
        default=False,
        verbose_name='Puede Re-ejecutarse'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Creado por'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Creación'
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Inicio'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Finalización'
    )

    class Meta:
        verbose_name = 'Trabajo de Importación'
        verbose_name_plural = 'Trabajos de Importación'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.importer_name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def duration(self):
        """Calculate duration of import"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

    @property
    def success_rate(self):
        """Calculate success rate percentage"""
        if self.total_rows > 0:
            return (self.success_rows / self.total_rows) * 100
        return 0

    @property
    def progress_percentage(self):
        """Calculate progress percentage"""
        if self.total_rows > 0:
            return (self.processed_rows / self.total_rows) * 100
        return 0

    def add_progress_log(self, message, level='info'):
        """Add a log entry to progress_log"""
        if self.progress_log is None:
            self.progress_log = []

        log_entry = {
            'timestamp': timezone.now().isoformat(),
            'message': message,
            'level': level,
            'processed': self.processed_rows,
            'total': self.total_rows
        }
        self.progress_log.append(log_entry)
        self.save(update_fields=['progress_log'])


class ImporterPermission(models.Model):
    """
    Proxy model to manage custom importer permissions.

    This model doesn't create a database table. It exists solely to hold
    dynamic permissions for each registered importer. Permissions are
    synced automatically during migrations.
    """

    class Meta:
        managed = False  # Don't create a database table
        default_permissions = ()  # Don't create standard add/change/delete/view permissions
        permissions = []  # Will be populated dynamically by registry
