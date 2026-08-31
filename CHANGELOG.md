# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.1] - 2026-08-31

### Fixed
- **Contraste en modo día/noche** (wizard y vista de detalle del job):
  - El wizard ahora tiene **paleta adaptable**: clara por defecto, oscura si
    el navegador está en modo noche (`prefers-color-scheme`) o si el host
    declara `data-theme="dark"` (Django ≥ 4.2). Antes la paleta era oscura
    fija.
  - **Blindaje contra el CSS global del admin host**: jet/jet-reboot pintan
    `table{background:#fff}` y `thead th` con sus propios colores en TODAS
    las tablas de la página, lo que dejaba el texto claro del wizard sobre
    filas blancas (mapeo y vista previa ilegibles). Ahora cada superficie y
    su texto se fijan explícitamente con `!important` dentro de `.fxw`.
  - Vista de detalle: el contenedor pinta siempre su propio fondo (el título
    quedaba ilegible al depender del fondo del host + auto-dark del
    navegador), el `h1` se fija con `!important` contra overrides del admin,
    el tema se aplica antes del primer render (sin flash) y reacciona si el
    usuario cambia el modo del navegador con la página abierta.
  - Overlay y spinner del wizard usan la paleta (antes hardcodeaban colores
    oscuros); el botón "Nueva Importación" del changelist fija `color:#fff`.

## [1.4.0] - 2026-08-19

### Added
- **Wizard de importación** (rediseño completo de la pantalla "Importar Datos"):
  stepper de 4 pasos (Archivo → Mapeo → Validación → Importar), compacto y
  con soporte dark/light del admin.
- **Drag & drop** del archivo (además de clic), con detección automática del
  formato por extensión (ya no se selecciona el formato a mano).
- **Mapeo interactivo de columnas**: si los encabezados del archivo no
  coinciden con los del importador, se propone un auto-mapeo (por nombre
  exacto y normalizado — sin acentos/mayúsculas/underscores) y el usuario
  puede ajustar campo por campo viendo una muestra de datos de cada columna.
- **Validación previa del archivo completo** con resumen por campo (conteo de
  errores + ejemplos con número de fila), detección de claves duplicadas
  (`key_field`) y vista previa de los datos ya limpios con celdas
  problemáticas resaltadas.
- **Limpieza de datos configurable**: recorte/colapso de espacios, números
  como texto (42.0 → "42"), coma decimal latina (1.234,56), fechas flexibles
  (múltiples formatos + serial de Excel) — con revalidación en vivo.
- Al iniciar, el wizard genera un **archivo XLSX normalizado** (encabezados y
  tipos ya correctos, filas con errores opcionalmente omitidas) que entra por
  el pipeline existente: sin migraciones ni cambios de modelo. Máxima
  probabilidad de importación al 100%.
- Nuevos endpoints admin: `import/preview/`, `import/validate/`,
  `import/start/` (respetan permisos `can_use_*` por importador).
- Setting `FLEX_IMPORTER_MAX_UPLOAD_MB` (default 20).
- Lectura CSV más robusta: BOM, detección de delimitador (`,` `;` tab `|`) y
  fallback de codificación utf-8 → cp1252 → latin-1.

### Fixed
- `validate_row()` perdía valores falsy legítimos (0, 0.0, False) en campos
  requeridos por usar `or` entre el lookup por nombre y por verbose_name.
- `_convert_field_value('date')` devolvía datetime completo cuando la celda
  era datetime; ahora devuelve `date` puro.

### Hardened (revisión adversarial multi-agente, 2026-08-19)
- Strings que inician con `=` se escriben como TEXTO en el XLSX normalizado
  (bloquea inyección de fórmulas y la pérdida silenciosa con `data_only=True`).
- Caracteres de control ilegales para XML se remueven en la limpieza (antes:
  `IllegalCharacterError` al generar el normalizado).
- Números: negativos contables `(1.234,56)` y `123-` conservan el signo;
  enteros/decimales largos desde texto se convierten SIN pasar por float
  (sin pérdida de dígitos).
- Datetimes con zona horaria se convierten a la hora local del proyecto antes
  de volverse naive (antes se descartaba el offset → corrimiento de horas).
- Columna `_fila_original` en el normalizado + soporte en el processor: los
  errores del job referencian la fila del archivo que subió el usuario.
- El normalizado respeta `Meta.header_row` del importador.
- `validate_row` se invoca sobre una INSTANCIA con claves por name y
  verbose_name (soporta los overrides de instancia existentes) y dentro de
  try/except.
- Con "importar filas con errores", el valor crudo que falló limpieza se
  conserva como texto (el processor reporta el error real, sin borrar datos).
- Fail-fast si el importador tiene `verbose_name` duplicados (colisionarían
  en el normalizado).
- `_sanitize_mapping` inmune a NaN/Infinity/floats del JSON.
- El archivo temporal se elimina ANTES de crear el ImportJob (un reintento
  con el mismo token no duplica la importación).
- Setting `FLEX_IMPORTER_MAX_ROWS` (default 100000) acota la memoria.
- Encabezados vacíos intermedios ya no ocultan las columnas a su derecha
  (se nombran "Columna N").
- UI: eventos `change` escuchados también vía jQuery (django-jet/Select2 no
  dispara eventos DOM nativos), guard de requests en vuelo (sin dobles
  importaciones), revalidación automática con debounce al cambiar la
  limpieza, paleta oscura autocontenida, `beforeunload` guard, accesibilidad
  (aria-live, aria-label, aria-current, focus-visible).

## [1.2.4] - 2026-01-18

### Fixed
- Fixed PyPI package missing `cleanup_stalled_imports` management command
- Package now correctly includes all new management commands and Celery tasks

## [1.2.3] - 2026-01-17

### Added
- **String Return Values Support**: `import_action()` now supports returning strings directly
  - Can return `'created'`, `'updated'`, or `'skipped'`
  - Backward compatible with legacy `True`/`None` return values
  - Also supports dict format: `{'action': 'created'}`
  - Documentation updated in QUICKSTART.md with examples
- **Stalled Jobs Detection**: New system to detect and handle stuck import jobs
  - `ImportJob.is_stalled()` method to check if a job is stuck
  - `ImportJob.mark_as_failed_if_stalled()` to mark stalled jobs as failed
  - `cleanup_stalled_imports` management command for manual cleanup
  - `cleanup_stalled_imports_task` Celery task for automatic periodic cleanup
  - Comprehensive guide in STALLED_JOBS_GUIDE.md

### Fixed
- Fixed issue where string return values like `'created'` were treated as errors
- Improved error handling to distinguish between valid action strings and actual errors
- Added protection against jobs getting stuck in 'pending' state when Celery worker is not running

## [1.2.2] - 2026-01-17

### Fixed
- **Critical Bug**: Fixed `validate_row()` method call in processor
  - Was calling as class method instead of instance method
  - This caused "missing 1 required positional argument: 'row_data'" error
  - Now correctly calls `importer_instance.validate_row()` instead of `self.importer_class.validate_row()`

### Added
- Comprehensive `validate_row` documentation in QUICKSTART.md
  - Explained that method MUST return tuple `(validated_data, errors)`
  - Added complete example with field validation
  - Included common mistakes and important notes

## [1.2.1] - 2026-01-17

### Added
- **Hybrid Auto-Sync for Permissions**: Permissions now sync automatically in multiple scenarios
  - Always syncs during `migrate` (production-safe)
  - Auto-syncs on Django startup in DEBUG mode (development convenience)
  - Configurable via `FLEX_IMPORTER_AUTO_SYNC_PERMISSIONS` setting
- **Development Convenience**: New importers get permissions automatically without running migrate in DEBUG mode

### Changed
- Updated `FlexImporterConfig.ready()` to include configurable auto-sync based on DEBUG mode
- Enhanced logging: Only logs when permissions are actually created/deleted to reduce noise
- Updated README.md with comprehensive auto-sync documentation and configuration options

### Why This Change?

This ensures that permissions are always in sync in any project using `django-flex-importer`:
- In development: Developers can add new importers and see permissions immediately
- In production: Permissions sync during migrate or server restart (no DEBUG overhead)
- Fully configurable: Users can customize behavior via settings

## [1.2.0] - 2026-01-17

### Added
- **Dynamic Permissions System**: Automatic permission generation for each registered importer
  - Permissions are auto-created during migrations via post_migrate signal
  - Permissions are auto-deleted when importers are removed from the codebase
  - Permission format: `can_use_<importername>` (e.g., `can_use_salesimporter`)
  - Full integration with Django's permission system (users and groups)
- **Permission-based Access Control** in Django Admin:
  - Users only see importers they have permission to use
  - Superusers have access to all importers by default
  - Security check prevents unauthorized access attempts
- **New Management Command**: `sync_importer_permissions`
  - Manually sync permissions with registered importers
  - `--dry-run` option to preview changes without applying them
- **New Model**: `ImporterPermission` proxy model to manage custom permissions
- **Registry Enhancements**:
  - `get_permission_codename()` method to get permission codename for an importer
  - `get_permission_name()` method to get human-readable permission name
  - `sync_permissions()` method to create/update/delete permissions

### Changed
- Updated `ImportForm` to filter importers based on user permissions
- Enhanced `import_view` in admin to verify permissions before processing imports
- Updated documentation in README.md with complete permissions guide

## [1.1.0] - 2026-01-17

### Changed
- **BREAKING**: Renamed `ImportLog` model to `ImportJob` to better reflect its purpose as a job execution record
- Updated all references throughout the codebase:
  - Admin interface (`ImportLogAdmin` → `ImportJobAdmin`)
  - Processor (parameter `import_log` → `import_job`)
  - Tasks (parameter `import_log_id` → `import_job_id`)
  - Management command (variable `logs` → `jobs`)
  - Templates (URL `importlog_changelist` → `importjob_changelist`)
- Database table automatically renamed from `flex_importer_importlog` to `flex_importer_importjob` via migration
- Updated verbose names in Spanish: "Bitácora de Importación" → "Trabajo de Importación"

### Migration Guide

If upgrading from v1.0.0:

1. **Update your package**:
   ```bash
   pip install --upgrade django-flex-importer
   ```

2. **Run migrations**:
   ```bash
   python manage.py migrate flex_importer
   ```
   This will automatically rename the database table and preserve all existing data.

3. **Update custom code** (if applicable):
   - If you have custom code that imports or references `ImportLog`, update it to use `ImportJob`:
     ```python
     # Old
     from flex_importer.models import ImportLog
     logs = ImportLog.objects.filter(status='success')

     # New
     from flex_importer.models import ImportJob
     jobs = ImportJob.objects.filter(status='success')
     ```

   - Update URL references:
     ```python
     # Old
     'admin:flex_importer_importlog_change'

     # New
     'admin:flex_importer_importjob_change'
     ```

4. **No changes needed** if you only use the Django admin interface - everything will work automatically!

### Why This Change?

The rename better reflects the model's purpose. Each `ImportJob` represents a complete execution of an import operation with its lifecycle (pending → processing → success/failed), not just a passive log entry.

## [1.0.0] - 2026-01-17

### Added
- Initial release of django-flex-importer
- `FlexImporter` base class for creating custom importers
- `FlexModelImporter` for automatic field extraction from Django models
- Support for XLSX, CSV, and JSON file formats
- Automatic field validation and type conversion
- `key_field` support for update/create operations
- Optional async processing with Celery
- Django Admin integration with:
  - Import form with file upload
  - Progress tracking with auto-refresh
  - Re-run capability for successful imports
  - Detailed statistics (created vs updated rows)
  - Error logging and reporting
- Complete documentation:
  - README with full API reference
  - QUICKSTART guide
  - KEY_FIELD_GUIDE for update operations
  - CELERY_SETUP for async configuration
  - TROUBLESHOOTING for common issues
  - CONTRIBUTING guide
- Example application with sample importers
- MIT License

[1.2.2]: https://github.com/twine003/django-flex-importer/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/twine003/django-flex-importer/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/twine003/django-flex-importer/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/twine003/django-flex-importer/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/twine003/django-flex-importer/releases/tag/v1.0.0
