"""
Ejemplo de cómo configurar limpieza automática de trabajos estancados.

Agrega esto a tu config/celery.py en tu proyecto.
"""

from celery import Celery
from celery.schedules import crontab
import os

# Configurar Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('myproject')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# ==============================================================================
# CONFIGURACIÓN DE TAREAS PERIÓDICAS
# ==============================================================================

app.conf.beat_schedule = {
    # Limpieza automática de trabajos estancados cada 5 minutos
    'cleanup-stalled-imports-every-5-minutes': {
        'task': 'flex_importer.cleanup_stalled_imports',
        'schedule': 300.0,  # 5 minutos en segundos
        'args': (10,),  # Timeout de 10 minutos
        'options': {
            'expires': 240,  # La tarea expira en 4 minutos si no se ejecuta
        }
    },

    # Alternativamente, puedes usar crontab para horarios específicos
    # Por ejemplo, cada hora en punto:
    # 'cleanup-stalled-imports-hourly': {
    #     'task': 'flex_importer.cleanup_stalled_imports',
    #     'schedule': crontab(minute=0),  # Cada hora en el minuto 0
    #     'args': (15,),  # Timeout de 15 minutos
    # },
}

# Configuración adicional de Celery (opcional pero recomendado)
app.conf.update(
    # Timezone
    timezone='America/Costa_Rica',  # Ajusta según tu ubicación

    # Habilitar UTC
    enable_utc=True,

    # Resultados
    result_expires=3600,  # Los resultados expiran en 1 hora

    # Logging
    worker_hijack_root_logger=False,
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s',
)

if __name__ == '__main__':
    app.start()
