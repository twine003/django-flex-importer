# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[1.1.0]: https://github.com/twine003/django-flex-importer/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/twine003/django-flex-importer/releases/tag/v1.0.0
