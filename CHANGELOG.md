# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.3] - 2026-01-17

### Added
- **String Return Values Support**: `import_action()` now supports returning strings directly
  - Can return `'created'`, `'updated'`, or `'skipped'`
  - Backward compatible with legacy `True`/`None` return values
  - Also supports dict format: `{'action': 'created'}`
  - Documentation updated in QUICKSTART.md with examples

### Fixed
- Fixed issue where string return values like `'created'` were treated as errors
- Improved error handling to distinguish between valid action strings and actual errors

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
