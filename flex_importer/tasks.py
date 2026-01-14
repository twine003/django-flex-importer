"""
Celery tasks for asynchronous import processing
"""
from .processor import ImportProcessor
from .models import ImportLog


def process_import_sync(import_log_id):
    """
    Synchronous fallback when Celery is not available.
    This is called directly when Celery is not configured.
    """
    try:
        import_log = ImportLog.objects.get(id=import_log_id)
        processor = ImportProcessor(import_log)
        processor.process()
        return True
    except ImportLog.DoesNotExist:
        return False
    except Exception as e:
        return False


try:
    # Try to import Celery
    from celery import shared_task

    @shared_task(bind=True, name='flex_importer.process_import')
    def process_import_async(self, import_log_id):
        """
        Asynchronous task for processing imports with Celery.

        Args:
            import_log_id: ID of the ImportLog to process

        Returns:
            bool: True if successful, False otherwise
        """
        return process_import_sync(import_log_id)

    CELERY_AVAILABLE = True

except ImportError:
    # Celery is not installed or configured
    process_import_async = None
    CELERY_AVAILABLE = False
