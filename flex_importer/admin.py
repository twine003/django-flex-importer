"""
Django admin for FlexImporter
"""
import json
import re
import uuid

from django.conf import settings
from django.contrib import admin
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django import forms
from . import wizard
from .models import ImportJob
from .registry import importer_registry
from .utils import should_use_async
from .tasks import process_import_async, process_import_sync

WIZARD_TMP_DIR = 'imports/tmp'
WIZARD_TOKEN_RE = re.compile(r'^[0-9a-f]{32}\.(xlsx|csv|json)$')


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
            path('import/preview/', self.admin_site.admin_view(self.import_preview_view), name='flex_importer_import_preview'),
            path('import/validate/', self.admin_site.admin_view(self.import_validate_view), name='flex_importer_import_validate'),
            path('import/start/', self.admin_site.admin_view(self.import_start_view), name='flex_importer_import_start'),
            path('download-template/', self.admin_site.admin_view(self.download_template_view), name='flex_importer_download_template'),
            path('<int:pk>/re-run/', self.admin_site.admin_view(self.re_run_view), name='flex_importer_re_run'),
            path('<int:pk>/retry/', self.admin_site.admin_view(self.retry_view), name='flex_importer_retry'),
            path('<int:pk>/progress/', self.admin_site.admin_view(self.progress_view), name='flex_importer_progress'),
            path('<int:pk>/data/', self.admin_site.admin_view(self.data_view), name='flex_importer_job_data'),
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

        importers_data = []
        allowed = self._allowed_importers(request.user)
        for class_path in sorted(allowed, key=lambda cp: str(allowed[cp].get_verbose_name())):
            importer_class = allowed[class_path]
            importers_data.append({
                'class_path': class_path,
                'verbose_name': str(importer_class.get_verbose_name()),
                'fields': wizard.public_field_info(importer_class),
                'key_field': importer_class.get_key_field() or '',
            })

        context = {
            **self.admin_site.each_context(request),
            'title': 'Importar Datos',
            'form': form,
            'opts': self.model._meta,
            'importers_json': json.dumps(importers_data, ensure_ascii=False),
            'cleaning_defaults_json': json.dumps(wizard.DEFAULT_CLEANING),
            'max_upload_mb': getattr(settings, 'FLEX_IMPORTER_MAX_UPLOAD_MB', 20),
        }

        return render(request, 'admin/flex_importer/import_form.html', context)

    # ------------------------------------------------------------------
    # Wizard de importación (endpoints JSON)
    # ------------------------------------------------------------------

    def _allowed_importers(self, user):
        """Importadores que el usuario puede usar (mismo criterio que ImportForm)."""
        allowed = {}
        for class_path, importer_class in importer_registry.get_all_importers().items():
            if user.is_superuser:
                allowed[class_path] = importer_class
                continue
            perm = importer_registry.get_permission_codename(importer_class)
            if user.has_perm(f'flex_importer.{perm}'):
                allowed[class_path] = importer_class
        return allowed

    def _wizard_importer_or_error(self, request, class_path):
        importer_class = importer_registry.get_importer(class_path)
        if not importer_class:
            return None, JsonResponse({'error': 'Importador no encontrado'}, status=404)
        if not request.user.is_superuser:
            perm = importer_registry.get_permission_codename(importer_class)
            if not request.user.has_perm(f'flex_importer.{perm}'):
                return None, JsonResponse(
                    {'error': 'No tiene permiso para usar este importador'}, status=403
                )
        return importer_class, None

    @staticmethod
    def _wizard_header_row(importer_class):
        return getattr(getattr(importer_class, 'Meta', None), 'header_row', 1)

    def _wizard_load_parsed(self, token, importer_class):
        if not token or not WIZARD_TOKEN_RE.match(token):
            raise ValueError('Token de archivo inválido')
        path = f'{WIZARD_TMP_DIR}/{token}'
        if not default_storage.exists(path):
            raise ValueError('El archivo temporal expiró. Vuelva a subir el archivo')
        file_format = token.rsplit('.', 1)[1]
        with default_storage.open(path, 'rb') as fh:
            return wizard.parse_file(
                fh, file_format, self._wizard_header_row(importer_class),
                max_rows=self._wizard_max_rows()
            )

    @staticmethod
    def _sanitize_mapping(raw_mapping, importer_class, n_headers):
        mapping = {}
        for info in importer_class.get_field_info():
            value = (raw_mapping or {}).get(info['name'])
            # solo índices enteros dentro de rango (NaN/Infinity de JSON
            # fallan is_integer() o la comparación y quedan en None)
            if (isinstance(value, (int, float)) and not isinstance(value, bool)
                    and float(value).is_integer() and 0 <= value < n_headers):
                mapping[info['name']] = int(value)
            else:
                mapping[info['name']] = None
        return mapping

    @staticmethod
    def _wizard_max_rows():
        return getattr(settings, 'FLEX_IMPORTER_MAX_ROWS', 100000)

    def _cleanup_stale_tmp(self):
        """Borra archivos temporales del wizard con más de 24h (best effort)."""
        try:
            _, files = default_storage.listdir(WIZARD_TMP_DIR)
            cutoff = timezone.now() - timezone.timedelta(hours=24)
            for name in files:
                if not WIZARD_TOKEN_RE.match(name):
                    continue
                path = f'{WIZARD_TMP_DIR}/{name}'
                if default_storage.get_modified_time(path) < cutoff:
                    default_storage.delete(path)
        except Exception:
            pass

    def import_preview_view(self, request):
        """Paso 1: recibe el archivo, lo guarda temporal y propone el mapeo."""
        if request.method != 'POST':
            return JsonResponse({'error': 'Método no permitido'}, status=405)

        upload = request.FILES.get('file')
        if not upload:
            return JsonResponse({'error': 'No se recibió ningún archivo'}, status=400)

        importer_class, error = self._wizard_importer_or_error(
            request, request.POST.get('importer', '')
        )
        if error:
            return error

        max_mb = getattr(settings, 'FLEX_IMPORTER_MAX_UPLOAD_MB', 20)
        if upload.size > max_mb * 1024 * 1024:
            return JsonResponse(
                {'error': f'El archivo supera el tamaño máximo de {max_mb} MB'}, status=400
            )

        file_format = wizard.detect_format(upload.name)
        if not file_format:
            return JsonResponse(
                {'error': 'Formato no soportado. Use un archivo XLSX, CSV o JSON'}, status=400
            )

        dup_verbose = wizard.duplicate_verbose_names(importer_class)
        if dup_verbose:
            return JsonResponse({
                'error': 'El importador tiene campos con verbose_name duplicado '
                         f'({", ".join(dup_verbose)}); corrija la definición del importador'
            }, status=400)

        try:
            parsed = wizard.parse_file(
                upload, file_format, self._wizard_header_row(importer_class),
                max_rows=self._wizard_max_rows()
            )
        except Exception as exc:
            return JsonResponse({'error': f'No se pudo leer el archivo: {exc}'}, status=400)

        if parsed.total == 0:
            return JsonResponse({'error': 'El archivo no contiene filas de datos'}, status=400)

        self._cleanup_stale_tmp()
        token = f'{uuid.uuid4().hex}.{file_format}'
        upload.seek(0)
        default_storage.save(f'{WIZARD_TMP_DIR}/{token}', upload)

        field_info = wizard.public_field_info(importer_class)
        auto_mapping = wizard.auto_map(parsed.headers, field_info)

        return JsonResponse({
            'token': token,
            'filename': upload.name,
            'format': file_format,
            'total_rows': parsed.total,
            'headers': [{'index': i, 'name': h} for i, h in enumerate(parsed.headers)],
            'sample_rows': [
                [wizard.display_value(v, 80) for v in row] for row in parsed.rows[:8]
            ],
            'fields': field_info,
            'auto_mapping': auto_mapping,
            'duplicate_headers': parsed.duplicate_headers(),
            'cleaning_defaults': wizard.DEFAULT_CLEANING,
        })

    def import_validate_view(self, request):
        """Paso 2/3: valida el dataset completo con el mapeo y limpieza dados."""
        if request.method != 'POST':
            return JsonResponse({'error': 'Método no permitido'}, status=405)
        try:
            payload = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'error': 'Cuerpo JSON inválido'}, status=400)

        importer_class, error = self._wizard_importer_or_error(
            request, payload.get('importer', '')
        )
        if error:
            return error

        try:
            parsed = self._wizard_load_parsed(payload.get('token', ''), importer_class)
        except ValueError as exc:
            return JsonResponse({'error': str(exc)}, status=400)
        except Exception as exc:
            return JsonResponse({'error': f'No se pudo leer el archivo: {exc}'}, status=400)

        mapping = self._sanitize_mapping(
            payload.get('mapping'), importer_class, len(parsed.headers)
        )
        data = wizard.validate_dataset(
            parsed, mapping, importer_class, payload.get('cleaning') or {}
        )
        return JsonResponse(data['resultado'])

    def import_start_view(self, request):
        """Paso final: genera el archivo normalizado, crea el ImportJob y lo lanza."""
        if request.method != 'POST':
            return JsonResponse({'error': 'Método no permitido'}, status=405)
        try:
            payload = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'error': 'Cuerpo JSON inválido'}, status=400)

        class_path = payload.get('importer', '')
        importer_class, error = self._wizard_importer_or_error(request, class_path)
        if error:
            return error

        token = payload.get('token', '')
        try:
            parsed = self._wizard_load_parsed(token, importer_class)
        except ValueError as exc:
            return JsonResponse({'error': str(exc)}, status=400)
        except Exception as exc:
            return JsonResponse({'error': f'No se pudo leer el archivo: {exc}'}, status=400)

        mapping = self._sanitize_mapping(
            payload.get('mapping'), importer_class, len(parsed.headers)
        )
        data = wizard.validate_dataset(
            parsed, mapping, importer_class, payload.get('cleaning') or {}
        )

        skip_invalid = bool(payload.get('skip_invalid', True))
        try:
            buffer, included, skipped = wizard.build_normalized_xlsx(
                parsed, data['cleaned_rows'], data['row_errors_list'],
                data['invalid_rows'], mapping, importer_class, skip_invalid,
                header_row=self._wizard_header_row(importer_class)
            )
        except Exception as exc:
            return JsonResponse(
                {'error': f'No se pudo generar el archivo normalizado: {exc}'}, status=400
            )
        if included == 0:
            return JsonResponse(
                {'error': 'No hay filas válidas para importar'}, status=400
            )

        # borrar el temporal ANTES de crear el job: un segundo click/reintento
        # con el mismo token recibe "expiró" en vez de duplicar la importación
        try:
            default_storage.delete(f'{WIZARD_TMP_DIR}/{token}')
        except Exception:
            pass

        original = str(payload.get('filename') or 'import')
        base_name = re.sub(r'[^\w.\-]+', '_', original).rsplit('.', 1)[0][:80]
        import_job = ImportJob.objects.create(
            importer_class=class_path,
            importer_name=importer_class.get_verbose_name(),
            file_format='xlsx',
            uploaded_file=ContentFile(buffer.read(), name=f'{base_name}_normalizado.xlsx'),
            can_re_run=importer_class.can_re_run(),
            created_by=request.user if request.user.is_authenticated else None,
        )
        if skipped:
            import_job.add_progress_log(
                f'Wizard: {skipped} filas con errores fueron omitidas del archivo normalizado',
                'warning'
            )

        if should_use_async():
            process_import_async.delay(import_job.id)
            async_mode = True
        else:
            process_import_sync(import_job.id)
            import_job.refresh_from_db()
            async_mode = False

        return JsonResponse({
            'job_id': import_job.id,
            'redirect': reverse('admin:flex_importer_importjob_change', args=[import_job.pk]),
            'async': async_mode,
            'incluidas': included,
            'omitidas': skipped,
        })

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

    def retry_view(self, request, pk):
        """View for retrying a pending/stalled import"""
        import_job = ImportJob.objects.get(pk=pk)

        # Only allow retry for pending (stalled) jobs
        if import_job.status != 'pending':
            self.message_user(
                request,
                'Solo se pueden reintentar importaciones en estado pendiente',
                level='error'
            )
            return redirect('admin:flex_importer_importjob_change', pk)

        # Reset the job status and counters
        import_job.status = 'pending'
        import_job.started_at = None
        import_job.completed_at = None
        import_job.total_rows = 0
        import_job.processed_rows = 0
        import_job.success_rows = 0
        import_job.created_rows = 0
        import_job.updated_rows = 0
        import_job.error_rows = 0
        import_job.error_details = []
        import_job.result_message = ''
        import_job.add_progress_log('Importación reiniciada manualmente', 'info')
        import_job.save()

        # Use async processing if Celery is available
        if should_use_async():
            process_import_async.delay(import_job.id)
            self.message_user(
                request,
                f'Importación #{import_job.id} reiniciada en segundo plano. '
                f'Puede monitorear el progreso en la página de detalle.'
            )
        else:
            # Process synchronously
            process_import_sync(import_job.id)
            import_job.refresh_from_db()
            self.message_user(request, f'Importación procesada: {import_job.result_message}')

        return redirect('admin:flex_importer_importjob_change', pk)

    def progress_view(self, request, pk):
        """API endpoint for progress updates"""
        # admin_view solo exige is_staff; el contenido del job requiere además
        # permiso de vista sobre ImportJob (hay instalaciones con staff limitado)
        if not self.has_view_permission(request):
            return JsonResponse({'error': 'Sin permiso para ver importaciones'}, status=403)
        import_job = ImportJob.objects.get(pk=pk)

        data = {
            'status': import_job.status,
            'status_display': import_job.get_status_display(),
            'total_rows': import_job.total_rows,
            'processed_rows': import_job.processed_rows,
            'success_rows': import_job.success_rows,
            'created_rows': import_job.created_rows,
            'updated_rows': import_job.updated_rows,
            'error_rows': import_job.error_rows,
            'progress_percentage': import_job.progress_percentage,
            'success_rate': import_job.success_rate,
            'progress_log': import_job.progress_log or [],
            'error_details': import_job.error_details[:50] if import_job.error_details else [],
            'error_details_total': len(import_job.error_details) if import_job.error_details else 0,
            'result_message': import_job.result_message,
            'can_re_run': import_job.can_re_run,
            'is_finished': import_job.status in ['success', 'partial', 'failed'],
        }

        return JsonResponse(data)

    DATA_PAGE_SIZE = 100

    def data_view(self, request, pk):
        """API JSON: contenido del archivo importado, paginado, para el modal
        "Ver datos" de la página de detalle del job."""
        # el archivo importado contiene datos personales: mismo requisito de
        # permiso que ver el ImportJob en el admin
        if not self.has_view_permission(request):
            return JsonResponse({'error': 'Sin permiso para ver importaciones'}, status=403)
        try:
            import_job = ImportJob.objects.get(pk=pk)
        except ImportJob.DoesNotExist:
            return JsonResponse({'error': 'Importación no encontrada'}, status=404)

        if not import_job.uploaded_file:
            return JsonResponse({'error': 'Esta importación no tiene archivo asociado'}, status=404)

        # header_row del importador (si sigue registrado); el archivo normalizado
        # del wizard se genera con este mismo header_row
        importer_class = importer_registry.get_importer(import_job.importer_class)
        header_row = self._wizard_header_row(importer_class) if importer_class else 1

        try:
            with import_job.uploaded_file.open('rb') as fh:
                parsed = wizard.parse_file(
                    fh, import_job.file_format, header_row,
                    max_rows=self._wizard_max_rows()
                )
        except FileNotFoundError:
            return JsonResponse(
                {'error': 'El archivo ya no está disponible en el almacenamiento'}, status=404
            )
        except Exception as exc:
            return JsonResponse({'error': f'No se pudo leer el archivo: {exc}'}, status=400)

        # la columna _fila_original (archivos normalizados por el wizard) se usa
        # como número de fila visible y no se muestra como columna de datos
        fila_col = None
        for i, h in enumerate(parsed.headers):
            if h == '_fila_original':
                fila_col = i
                break
        visible_idx = [i for i in range(len(parsed.headers)) if i != fila_col]

        # errores por número de fila (mismo esquema que usa el processor)
        errors_by_row = {}
        for err in (import_job.error_details or []):
            try:
                errors_by_row[int(err['row'])] = err.get('errors', [])
            except (KeyError, TypeError, ValueError):
                continue

        try:
            page = max(1, int(request.GET.get('page', 1)))
        except ValueError:
            page = 1
        total = parsed.total
        pages = max(1, -(-total // self.DATA_PAGE_SIZE))  # ceil
        page = min(page, pages)
        start = (page - 1) * self.DATA_PAGE_SIZE
        end = start + self.DATA_PAGE_SIZE

        rows = []
        for offset in range(start, min(end, total)):
            values = parsed.rows[offset]
            if fila_col is not None and values[fila_col] not in (None, ''):
                try:
                    row_number = int(float(values[fila_col]))
                except (TypeError, ValueError):
                    row_number = parsed.row_numbers[offset]
            else:
                row_number = parsed.row_numbers[offset]
            rows.append({
                'n': row_number,
                'values': [wizard.display_value(values[i], 120) for i in visible_idx],
                'errors': errors_by_row.get(row_number, []),
            })

        return JsonResponse({
            'filename': import_job.uploaded_file.name,
            'headers': [parsed.headers[i] for i in visible_idx],
            'rows': rows,
            'total': total,
            'page': page,
            'pages': pages,
            'page_size': self.DATA_PAGE_SIZE,
        })

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

        # Retry button for pending/stalled jobs only
        if obj.status == 'pending':
            url = reverse('admin:flex_importer_retry', args=[obj.pk])
            html.append(f'<a href="{url}" class="button" style="padding: 5px 10px; background-color: #ffc107; color: #212529; text-decoration: none; border-radius: 3px;" title="Reintentar esta importación">🔄 Reintentar</a>')

        # Re-run button for failed jobs only (not success/partial/processing to avoid duplicates)
        if obj.can_re_run and obj.status == 'failed':
            url = reverse('admin:flex_importer_re_run', args=[obj.pk])
            html.append(f'<a href="{url}" class="button" style="padding: 5px 10px; background-color: #17a2b8; color: white; text-decoration: none; border-radius: 3px;">Re-ejecutar</a>')

        return mark_safe(' '.join(html))
    actions_column.short_description = 'Acciones'

    def has_add_permission(self, request):
        """Disable add button"""
        return False

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Override change view to add re-run and retry buttons"""
        extra_context = extra_context or {}

        # Get the import job object
        import_job = self.get_object(request, object_id)

        if import_job:
            # Retry button for pending/stalled jobs only
            if import_job.status == 'pending':
                extra_context['show_retry_button'] = True
                extra_context['retry_url'] = reverse('admin:flex_importer_retry', args=[object_id])

            # Re-run button for failed jobs only (not success/partial/processing to avoid duplicates)
            if import_job.can_re_run and import_job.status == 'failed':
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
