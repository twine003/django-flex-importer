# Guía para Manejar Trabajos de Importación Estancados

## 📋 Problema

Cuando el worker de Celery no está corriendo o hay problemas con Redis, las importaciones asíncronas pueden quedarse atascadas en estado "Pendiente" sin procesarse nunca.

## ✅ Soluciones Implementadas

### 1. Comando Manual de Limpieza

Ejecuta este comando para detectar y marcar trabajos estancados como fallidos:

```bash
# Usar timeout por defecto (10 minutos)
python manage.py cleanup_stalled_imports

# Usar timeout personalizado
python manage.py cleanup_stalled_imports --timeout 15

# Ver qué se limpiaría sin hacerlo (dry-run)
python manage.py cleanup_stalled_imports --dry-run
```

**Salida de ejemplo:**

```
======================================================================
LIMPIEZA DE IMPORTACIONES ESTANCADAS (timeout: 10 min)
======================================================================

⚠️  Se encontraron 2 importaciones estancadas:

  • ID 14: Desalojo TAE
    Estado: pending
    Creado: 2026-01-17 03:55:10
    Tiempo transcurrido: 0h 25m 34s

  • ID 12: ABC Clientes
    Estado: processing
    Creado: 2026-01-17 02:30:15
    Tiempo transcurrido: 1h 50m 18s

Marcando trabajos como fallidos...

  ✅ Job ID 14 marcado como fallido
  ✅ Job ID 12 marcado como fallido

======================================================================
✅ Completado: 2 trabajos marcados como fallidos
======================================================================
```

### 2. Tarea Automática con Celery Beat

Configura Celery Beat para ejecutar la limpieza automáticamente cada 5 minutos.

#### En `config/celery.py`:

```python
from celery import Celery
from celery.schedules import crontab

app = Celery('django_importer')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Configurar tareas periódicas
app.conf.beat_schedule = {
    'cleanup-stalled-imports': {
        'task': 'flex_importer.cleanup_stalled_imports',
        'schedule': 300.0,  # Cada 5 minutos (en segundos)
        'args': (10,),  # Timeout de 10 minutos
    },
}
```

#### Iniciar Celery Beat:

```bash
# Terminal 1: Worker
celery -A config worker --loglevel=info

# Terminal 2: Beat scheduler
celery -A config beat --loglevel=info
```

### 3. Verificación Programática

Puedes verificar si un trabajo específico está estancado:

```python
from flex_importer.models import ImportJob

# Obtener el job
job = ImportJob.objects.get(id=14)

# Verificar si está estancado (timeout por defecto: 10 min)
if job.is_stalled():
    print("⚠️  Este trabajo está estancado")

    # Marcarlo como fallido
    if job.mark_as_failed_if_stalled():
        print("✅ Trabajo marcado como fallido")

# Usar timeout personalizado
if job.is_stalled(timeout_minutes=15):
    print("⚠️  Este trabajo está estancado (15 min)")
```

### 4. Cron Job (Sin Celery Beat)

Si no quieres usar Celery Beat, puedes configurar un cron job:

```bash
# Editar crontab
crontab -e

# Agregar esta línea para ejecutar cada 5 minutos
*/5 * * * * cd /path/to/project && /path/to/venv/bin/python manage.py cleanup_stalled_imports >> /var/log/import_cleanup.log 2>&1
```

## 🔍 Cómo Funciona la Detección

Un trabajo se considera estancado si:

1. **Estado "Pending"**:
   - Más de X minutos desde su creación sin cambiar a "processing"
   - Indica que el worker no lo tomó

2. **Estado "Processing"**:
   - Más de X minutos desde que comenzó sin procesar ninguna fila
   - Indica que el worker se detuvo en medio del proceso

## ⚙️ Configuración

### Ajustar el Timeout

El timeout por defecto es **10 minutos**. Puedes ajustarlo según:

- **Archivos pequeños** (< 1000 filas): 5-10 minutos
- **Archivos medianos** (1000-10000 filas): 10-15 minutos
- **Archivos grandes** (> 10000 filas): 15-30 minutos

### En el Comando:

```bash
python manage.py cleanup_stalled_imports --timeout 15
```

### En Celery Beat:

```python
'cleanup-stalled-imports': {
    'task': 'flex_importer.cleanup_stalled_imports',
    'schedule': 300.0,
    'args': (15,),  # 15 minutos
},
```

### En Código:

```python
job.is_stalled(timeout_minutes=15)
job.mark_as_failed_if_stalled(timeout_minutes=15)
```

## 📊 Monitoreo

### Ver Trabajos Pendientes/Procesando:

```python
from flex_importer.models import ImportJob
from django.utils import timezone

# Trabajos en estados activos
active_jobs = ImportJob.objects.filter(
    status__in=['pending', 'processing']
).order_by('created_at')

for job in active_jobs:
    time_elapsed = timezone.now() - job.created_at
    print(f"ID {job.id}: {job.importer_name}")
    print(f"  Estado: {job.status}")
    print(f"  Tiempo: {time_elapsed}")
    print(f"  Estancado: {job.is_stalled()}")
    print()
```

### Estadísticas:

```python
from flex_importer.models import ImportJob

# Contar trabajos estancados
stalled_count = sum(
    1 for job in ImportJob.objects.filter(status__in=['pending', 'processing'])
    if job.is_stalled()
)

print(f"Trabajos estancados: {stalled_count}")
```

## 🛠️ Troubleshooting

### Problema: Trabajos marcados como fallidos incorrectamente

**Solución:** Aumentar el timeout

```bash
python manage.py cleanup_stalled_imports --timeout 20
```

### Problema: Trabajos realmente estancados no se detectan

**Causas posibles:**
1. El worker de Celery no está corriendo
2. Redis no está disponible
3. Hay un error en el importador que causa un loop infinito

**Verificar:**

```bash
# Verificar Redis
redis-cli ping

# Verificar workers de Celery
celery -A config inspect active

# Ver logs del worker
celery -A config worker --loglevel=debug
```

### Problema: Muchos trabajos estancados frecuentemente

**Soluciones:**
1. **Asegurar que el worker esté siempre corriendo** (usar systemd/supervisor)
2. **Monitorear Redis** (asegurar que esté siempre disponible)
3. **Revisar errores en importadores** (pueden estar causando crashes)

## 📝 Mejores Prácticas

1. **Ejecutar cleanup regularmente:**
   - Usar Celery Beat cada 5-10 minutos
   - O cron job si no usas Celery Beat

2. **Monitorear el estado del worker:**
   - Usar herramientas como Flower para Celery
   - Configurar alertas si el worker se cae

3. **Logging adecuado:**
   - Los trabajos marcados como fallidos incluyen un mensaje explicativo
   - Revisar los logs para identificar problemas recurrentes

4. **Testing antes de producción:**
   - Probar con `--dry-run` primero
   - Ajustar timeout según tus necesidades

## 🔗 Ver También

- [CELERY_SETUP.md](CELERY_SETUP.md) - Configuración de Celery
- [CELERY_TEST.md](CELERY_TEST.md) - Pruebas de Celery
- [README.md](README.md) - Documentación general

---

## 🎯 Ejemplo Completo de Configuración

### 1. Configurar Celery Beat en `config/celery.py`:

```python
from celery import Celery
from celery.schedules import crontab

app = Celery('myproject')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # Limpieza automática de trabajos estancados
    'cleanup-stalled-imports': {
        'task': 'flex_importer.cleanup_stalled_imports',
        'schedule': 300.0,  # Cada 5 minutos
        'args': (10,),  # 10 minutos de timeout
    },
}
```

### 2. Iniciar servicios:

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Celery Worker
celery -A config worker --loglevel=info --pool=solo

# Terminal 3: Celery Beat
celery -A config beat --loglevel=info
```

### 3. Verificar que funciona:

```bash
# Ver tareas programadas
celery -A config inspect scheduled

# Ver tareas activas
celery -A config inspect active

# Ver logs de Beat
# Deberías ver cada 5 minutos:
# [2026-01-17 15:30:00] Task flex_importer.cleanup_stalled_imports[...] received
```

¡Listo! Ahora tus trabajos estancados se detectarán y marcarán como fallidos automáticamente.
