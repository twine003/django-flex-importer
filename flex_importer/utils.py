"""
Utility functions for flex_importer
"""


def is_celery_available():
    """
    Check if Celery is available and properly configured.

    Returns:
        bool: True if Celery is available and configured, False otherwise
    """
    try:
        from celery import current_app
        from django.conf import settings

        # Check if Celery is imported
        if not current_app:
            return False

        # Check if broker is configured
        broker_url = getattr(settings, 'CELERY_BROKER_URL', None)
        if not broker_url:
            return False

        # Try to ping the broker (with timeout)
        try:
            inspect = current_app.control.inspect(timeout=1.0)
            if inspect is None:
                return False
            # Check if any workers are active
            stats = inspect.stats()
            return stats is not None and len(stats) > 0
        except Exception:
            # If we can't inspect, assume Celery is configured but workers might not be running
            # Still return True so tasks get queued
            return True

    except ImportError:
        return False
    except Exception:
        return False


def should_use_async(threshold=100):
    """
    Determine if async processing should be used based on Celery availability.

    Args:
        threshold: Minimum number of rows to trigger async processing (not used if Celery unavailable)

    Returns:
        bool: True if async should be used, False for sync processing
    """
    return is_celery_available()
