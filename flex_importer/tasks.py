"""
Celery tasks for asynchronous import processing
"""
from .processor import ImportProcessor
from .models import ImportJob


def process_import_sync(import_job_id):
    """
    Synchronous fallback when Celery is not available.
    This is called directly when Celery is not configured.
    """
    try:
        import_job = ImportJob.objects.get(id=import_job_id)
        processor = ImportProcessor(import_job)
        processor.process()
        return True
    except ImportJob.DoesNotExist:
        return False
    except Exception as e:
        return False


try:
    # Try to import Celery
    from celery import shared_task

    @shared_task(bind=True, name='flex_importer.process_import')
    def process_import_async(self, import_job_id):
        """
        Asynchronous task for processing imports with Celery.

        Args:
            import_job_id: ID of the ImportJob to process

        Returns:
            bool: True if successful, False otherwise
        """
        return process_import_sync(import_job_id)

    @shared_task(name='flex_importer.cleanup_stalled_imports')
    def cleanup_stalled_imports_task(timeout_minutes=10):
        """
        Periodic task to detect and cleanup stalled import jobs.

        This task should be scheduled to run periodically (e.g., every 5 minutes)
        to automatically detect and mark stalled jobs as failed.

        Args:
            timeout_minutes: Minutes to wait before considering a job stalled

        Returns:
            int: Number of jobs marked as failed
        """
        marked_count = 0
        stalled_jobs = []

        # Find stalled jobs
        for job in ImportJob.objects.filter(status__in=['pending', 'processing']):
            if job.is_stalled(timeout_minutes):
                stalled_jobs.append(job)

        # Mark them as failed
        for job in stalled_jobs:
            if job.mark_as_failed_if_stalled(timeout_minutes):
                marked_count += 1

        return marked_count

    CELERY_AVAILABLE = True

except ImportError:
    # Celery is not installed or configured
    process_import_async = None
    cleanup_stalled_imports_task = None
    CELERY_AVAILABLE = False
