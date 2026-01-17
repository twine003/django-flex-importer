"""
Django admin for FlexImporter
"""
from django.contrib import admin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django import forms
from .models import ImportJob
from .registry import importer_registry
from .utils import should_use_async
from .tasks import process_import_async, process_import_sync
import json


class ImportForm(forms.Form):
    """Form for selecting importer and uploading file"""

    importer = forms.ChoiceField(
        label='Importador',
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    file_format = forms.ChoiceField(
        label='Formato',
        choices=ImportJob.FORMAT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    file = forms.FileField(
        label='Archivo',
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter importers based on user permissions
        if user and user.is_authenticated:
            allowed_choices = []
            for class_name, importer_class in importer_registry.get_all_importers().items():
                # Superusers can see all importers
                if user.is_superuser:
                    allowed_choices.append((class_name, importer_class.get_verbose_name()))
                else:
                    # Check if user has permission for this importer
                    perm_codename = importer_registry.get_permission_codename(importer_class)
                    if user.has_perm(f'flex_importer.{perm_codename}'):
                        allowed_choices.append((class_name, importer_class.get_verbose_name()))
            self.fields['importer'].choices = sorted(allowed_choices, key=lambda x: x[1])
        else:
            self.fields['importer'].choices = importer_registry.get_importer_choices()


@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    """Admin for ImportJob model"""

    list_display = [
        'id',
        'importer_name',
        'file_format',
        'status_badge',
        'progress_bar',
        'success_rate_display',
        'created_at',
        'actions_column'
    ]
    list_filter = ['status', 'file_format', 'created_at']
    search_fields = ['importer_name', 'importer_class']
    readonly_fields = [
        'importer_class',
        'importer_name',
        'file_format',
        'uploaded_file',
        'status',
        'total_rows',
        'processed_rows',
        'success_rows',
        'created_rows',
        'updated_rows',
        'error_rows',
        'error_details_display',
        'progress_log_display',
        'result_message',
        'can_re_run',
        'created_by',
        'created_at',
        'started_at',
        'completed_at',
        'duration_display',
        'success_rate_display'
    ]

    fieldsets = (
        ('Información General', {
            'fields': (
                'importer_name',
                'importer_class',
                'file_format',
                'uploaded_file',
                'status',
                'can_re_run'
            )
        }),
        ('Estadísticas', {
            'fields': (
                'total_rows',
                'processed_rows',
                'success_rows',
                'created_rows',
                'updated_rows',
                'error_rows',
                'success_rate_display',
            )
        }),
        ('Resultados', {
            'fields': (
                'result_message',
                'error_details_display',
                'progress_log_display',
            )
        }),
        ('Fechas', {
            'fields': (
                'created_at',
                'created_by',
                'started_at',
                'completed_at',
                'duration_display',
            )
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import/', self.admin_site.admin_view(self.import_view), name='flex_importer_import'),
            path('download-template/', self.admin_site.admin_view(self.download_template_view), name='flex_importer_download_template'),
            path('<int:pk>/re-run/', self.admin_site.admin_view(self.re_run_view), name='flex_importer_re_run'),
            path('<int:pk>/progress/', self.admin_site.admin_view(self.progress_view), name='flex_importer_progress'),
        ]
        return custom_urls + urls

    def import_view(self, request):
        """View for importing data"""
        if request.method == 'POST':
            form = ImportForm(user=request.user, data=request.POST, files=request.FILES)
            if form.is_valid():
                importer_class_name = form.cleaned_data['importer']
                file_format = form.cleaned_data['file_format']
                uploaded_file = form.cleaned_data['file']

                importer_class = importer_registry.get_importer(importer_class_name)

                # Verify user has permission (security check)
                if not request.user.is_superuser:
                    perm_codename = importer_registry.get_permission_codename(importer_class)
                    if not request.user.has_perm(f'flex_importer.{perm_codename}'):
                        self.message_user(request, 'No tiene permiso para usar este importador', level='error')
                        return redirect('admin:flex_importer_importjob_changelist')

                import_job = ImportJob.objects.create(
                    importer_class=importer_class_name,
                    importer_name=importer_class.get_verbose_name(),
                    file_format=file_format,
                    uploaded_file=uploaded_file,
                    can_re_run=importer_class.can_re_run(),
                    created_by=request.user if request.user.is_authenticated else None
                )

                # Use async processing if Celery is available
                if should_use_async():
                    # Queue the task
                    process_import_async.delay(import_job.id)
                    self.message_user(
                        request,
                        f'Importación iniciada en segundo plano. ID: {import_job.id}. '
                        f'Puede monitorear el progreso en la página de detalle.'
                    )
                else:
                    # Process synchronously
                    process_import_sync(import_job.id)
                    # Refresh to get updated status
                    import_job.refresh_from_db()
                    self.message_user(request, f'Importación procesada: {import_job.result_message}')

                return redirect('admin:flex_importer_importjob_change', import_job.pk)
        else:
            form = ImportForm(user=request.user)

        context = {
            **self.admin_site.each_context(request),
            'title': 'Importar Datos',
            'form': form,
            'opts': self.model._meta,
        }

        return render(request, 'admin/flex_importer/import_form.html', context)

    def download_template_view(self, request):
        """View for downloading templates"""
        importer_class_name = request.GET.get('importer')
        file_format = request.GET.get('format', 'xlsx')

        if not importer_class_name:
            return HttpResponse('Debe especificar un importador', status=400)

        importer_class = importer_registry.get_importer(importer_class_name)
        if not importer_class:
            return HttpResponse('Importador no encontrado', status=404)

        if file_format == 'xlsx':
            buffer = importer_class.generate_template_xlsx()
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = f'template_{importer_class.__name__}.xlsx'
        elif file_format == 'csv':
            buffer = importer_class.generate_template_csv()
            content_type = 'text/csv'
            filename = f'template_{importer_class.__name__}.csv'
        elif file_format == 'json':
            buffer = importer_class.generate_template_json()
            content_type = 'application/json'
            filename = f'template_{importer_class.__name__}.json'
        else:
            return HttpResponse('Formato no soportado', status=400)

        response = HttpResponse(buffer.read(), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    def re_run_view(self, request, pk):
        """View for re-running an import"""
        import_job = ImportJob.objects.get(pk=pk)

        if not import_job.can_re_run:
            self.message_user(request, 'Esta importación no puede ser re-ejecutada', level='error')
            return redirect('admin:flex_importer_importjob_changelist')

        new_import_job = ImportJob.objects.create(
            importer_class=import_job.importer_class,
            importer_name=import_job.importer_name,
            file_format=import_job.file_format,
            uploaded_file=import_job.uploaded_file,
            can_re_run=import_job.can_re_run,
            created_by=request.user if request.user.is_authenticated else None
        )

        # Use async processing if Celery is available
        if should_use_async():
            # Queue the task
            process_import_async.delay(new_import_job.id)
            self.message_user(
                request,
                f'Re-ejecución iniciada en segundo plano. ID: {new_import_job.id}. '
                f'Puede monitorear el progreso en la página de detalle.'
            )
        else:
            # Process synchronously
            process_import_sync(new_import_job.id)
            # Refresh to get updated status
            new_import_job.refresh_from_db()
            self.message_user(request, f'Importación re-ejecutada: {new_import_job.result_message}')

        return redirect('admin:flex_importer_importjob_change', new_import_job.pk)

    def progress_view(self, request, pk):
        """API endpoint for progress updates"""
        import_job = ImportJob.objects.get(pk=pk)

        data = {
            'status': import_job.status,
            'total_rows': import_job.total_rows,
            'processed_rows': import_job.processed_rows,
            'success_rows': import_job.success_rows,
            'error_rows': import_job.error_rows,
            'progress_percentage': import_job.progress_percentage,
            'progress_log': import_job.progress_log or [],
            'result_message': import_job.result_message,
        }

        return JsonResponse(data)

    def status_badge(self, obj):
        """Display status as badge"""
        colors = {
            'pending': '#ffc107',
            'processing': '#17a2b8',
            'success': '#28a745',
            'partial': '#fd7e14',
            'failed': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'

    def progress_bar(self, obj):
        """Display progress bar"""
        percentage = obj.progress_percentage
        color = '#17a2b8' if obj.status == 'processing' else '#28a745'

        if obj.status in ['success', 'partial', 'failed']:
            color = '#28a745' if obj.status == 'success' else '#fd7e14' if obj.status == 'partial' else '#dc3545'

        return format_html(
            '<div style="width: 100px; background-color: #e9ecef; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; color: white; text-align: center; border-radius: 3px; padding: 2px;">{}%</div>'
            '</div>',
            percentage, color, int(percentage)
        )
    progress_bar.short_description = 'Progreso'

    def success_rate_display(self, obj):
        """Display success rate"""
        return f'{obj.success_rate:.1f}%'
    success_rate_display.short_description = 'Tasa de Éxito'

    def duration_display(self, obj):
        """Display duration"""
        duration = obj.duration
        if duration:
            return str(duration).split('.')[0]
        return '-'
    duration_display.short_description = 'Duración'

    def error_details_display(self, obj):
        """Display error details"""
        if not obj.error_details:
            return '-'

        html = '<div style="max-height: 400px; overflow-y: auto;">'
        for error in obj.error_details[:50]:
            html += f'<div style="margin-bottom: 10px; padding: 10px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 3px;">'
            html += f'<strong>Fila {error["row"]}:</strong><br>'
            for err in error['errors']:
                html += f'• {err}<br>'
            html += '</div>'

        if len(obj.error_details) > 50:
            html += f'<p>... y {len(obj.error_details) - 50} errores más</p>'

        html += '</div>'
        return mark_safe(html)
    error_details_display.short_description = 'Detalles de Errores'

    def progress_log_display(self, obj):
        """Display progress log"""
        if not obj.progress_log:
            return '-'

        html = '<div style="max-height: 400px; overflow-y: auto; background-color: #f8f9fa; padding: 10px; border-radius: 3px; font-family: monospace; font-size: 12px;">'

        for log_entry in obj.progress_log:
            level = log_entry.get('level', 'info')
            color = '#28a745' if level == 'success' else '#ffc107' if level == 'warning' else '#dc3545' if level == 'error' else '#17a2b8'

            html += f'<div style="margin-bottom: 5px;">'
            html += f'<span style="color: {color};">[{log_entry["timestamp"]}]</span> '
            html += f'{log_entry["message"]}'
            html += '</div>'

        html += '</div>'
        return mark_safe(html)
    progress_log_display.short_description = 'Log de Progreso'

    def actions_column(self, obj):
        """Display action buttons"""
        html = []

        if obj.can_re_run and obj.status in ['success', 'partial', 'failed']:
            url = reverse('admin:flex_importer_re_run', args=[obj.pk])
            html.append(f'<a href="{url}" class="button" style="padding: 5px 10px; background-color: #17a2b8; color: white; text-decoration: none; border-radius: 3px;">Re-ejecutar</a>')

        return mark_safe(' '.join(html))
    actions_column.short_description = 'Acciones'

    def has_add_permission(self, request):
        """Disable add button"""
        return False

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Override change view to add re-run button"""
        extra_context = extra_context or {}

        # Get the import job object
        import_job = self.get_object(request, object_id)

        if import_job and import_job.can_re_run and import_job.status in ['success', 'partial', 'failed']:
            extra_context['show_rerun_button'] = True
            extra_context['rerun_url'] = reverse('admin:flex_importer_re_run', args=[object_id])

            # Check if the importer has key_field
            from .registry import importer_registry
            importer_class = importer_registry.get_importer(import_job.importer_class)
            if importer_class:
                key_field = importer_class.get_key_field()
                extra_context['has_key_field'] = bool(key_field)

        return super().change_view(request, object_id, form_url, extra_context)

    def changelist_view(self, request, extra_context=None):
        """Override changelist to add import button"""
        extra_context = extra_context or {}
        extra_context['show_import_button'] = True
        return super().changelist_view(request, extra_context)
