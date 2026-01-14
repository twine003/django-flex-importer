# Configuración de Celery para Importaciones Asíncronas

## ¿Por qué usar Celery?

Para importaciones con **miles de registros**, procesar de forma síncrona puede:
- Hacer que el navegador se quede esperando por minutos
- Causar timeouts en el servidor web
- Bloquear el proceso de Django

**Celery** resuelve esto procesando las importaciones en **segundo plano** (asíncrono), permitiendo:
- ✅ Respuesta inmediata al usuario
- ✅ Procesar miles de registros sin bloquear el servidor
- ✅ Monitorear el progreso en tiempo real
- ✅ Continuar trabajando mientras la importación se ejecuta

## Detección Automática

El sistema **detecta automáticamente** si Celery está disponible:

- **Con Celery configurado**: Las importaciones se procesan en segundo plano
- **Sin Celery**: Las importaciones se procesan de forma síncrona (como antes)

No necesitas cambiar tu código. El sistema se adapta automáticamente.

## Instalación de Celery

### 1. Instalar Celery y un broker

```bash
# Opción 1: Redis (recomendado)
pip install celery redis

# Opción 2: RabbitMQ
pip install celery
# Luego instalar RabbitMQ en tu sistema
```

### 2. Instalar Redis (si elegiste Redis)

**Windows:**
```bash
# Opción 1: Usar Docker
docker run -d -p 6379:6379 redis

# Opción 2: Descargar Redis para Windows
# https://github.com/microsoftarchive/redis/releases
```

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# Mac
brew install redis

# Iniciar Redis
redis-server
```

### 3. Configurar Django

Agrega esto a tu `settings.py`:

```python
# Celery Configuration (opcional - solo si quieres usar async)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Mexico_City'  # Ajusta a tu zona horaria
```

**Nota:** El archivo `config/celery.py` ya está incluido en el proyecto.

### 4. Iniciar el worker de Celery

En una terminal separada, ejecuta:

```bash
# Activar tu entorno virtual primero
pyenv activate django-importer  # o tu comando para activar el venv

# Iniciar el worker
celery -A config worker --loglevel=info

# En Windows, puede que necesites usar:
celery -A config worker --loglevel=info --pool=solo
```

## Verificar que Celery está funcionando

### Método 1: Usar el comando de Django

```bash
python manage.py shell
```

Luego en la shell:

```python
from flex_importer.utils import is_celery_available

print("¿Celery disponible?", is_celery_available())
# Debe mostrar: True
```

### Método 2: Revisar el log del admin

Cuando crees una importación:

**Con Celery:**
```
Importación iniciada en segundo plano. ID: 123.
Puede monitorear el progreso en la página de detalle.
```

**Sin Celery:**
```
Importación procesada: Importación completada exitosamente. 100 filas procesadas.
```

## Comportamiento del Sistema

### Sin Celery (Síncrono)

1. Usuario sube archivo
2. **Espera** mientras se procesa
3. Ve el resultado cuando termina

```
Usuario → Importa → [Espera...] → Resultado
```

### Con Celery (Asíncrono)

1. Usuario sube archivo
2. **Redirección inmediata** a página de detalle
3. Página se auto-actualiza cada 5 segundos
4. Ve el progreso en tiempo real

```
Usuario → Importa → Redirección inmediata
                  ↓
            Worker de Celery procesa en background
                  ↓
            Auto-refresh muestra progreso
                  ↓
            Resultado final
```

## Monitoreo de Importaciones Asíncronas

Cuando una importación se procesa con Celery:

### 1. Notificación Visual

Verás un banner azul en la página de detalle:

```
⏳ Importación en progreso
Esta página se actualizará automáticamente cada 5 segundos hasta que la importación finalice.
Procesando fila 150 de 1000...
```

### 2. Auto-refresh

La página se recarga automáticamente cada 5 segundos mientras el estado sea `pending` o `processing`.

### 3. Estados de la Importación

- **Pending** (Pendiente): En cola, esperando a ser procesada
- **Processing** (Procesando): Siendo procesada por un worker
- **Success** (Éxito): Completada sin errores
- **Partial** (Parcial): Completada con algunos errores
- **Failed** (Fallida): Falló completamente

## Ejemplo de Configuración Completa

### settings.py

```python
# ... otras configuraciones ...

# Celery (opcional)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
```

### Iniciar el proyecto con Celery

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Django
python manage.py runserver

# Terminal 3: Celery Worker
celery -A config worker --loglevel=info
```

## Solución de Problemas

### Problema: "Celery no está disponible"

**Verificar:**

1. Redis está corriendo:
   ```bash
   redis-cli ping
   # Debe responder: PONG
   ```

2. Worker de Celery está corriendo:
   ```bash
   celery -A config inspect active
   # Debe mostrar workers activos
   ```

3. Configuración en settings.py:
   ```python
   print(settings.CELERY_BROKER_URL)
   # Debe mostrar: redis://localhost:6379/0
   ```

### Problema: Las tareas se encolan pero no se procesan

**Causa:** No hay workers corriendo o el worker no puede conectarse a Redis.

**Solución:**

1. Asegúrate de que Redis está corriendo
2. Inicia el worker: `celery -A config worker --loglevel=info`
3. Revisa los logs del worker para ver errores

### Problema: ImportError al iniciar Celery

**Error:** `ImportError: cannot import name 'celery_app'`

**Solución:** Verifica que `config/__init__.py` tenga el import de celery dentro de un try/except.

### Problema: En Windows el worker no funciona

**Solución:** Usa el flag `--pool=solo`:

```bash
celery -A config worker --loglevel=info --pool=solo
```

## Modo de Desarrollo vs Producción

### Desarrollo (sin Celery)

Para desarrollo rápido, **no necesitas Celery**. Las importaciones se procesan síncronamente.

```bash
# Solo necesitas:
python manage.py runserver
```

### Producción (con Celery)

Para producción con importaciones grandes:

```bash
# Necesitas:
1. Redis corriendo
2. Django corriendo (gunicorn/uwsgi)
3. Worker(s) de Celery corriendo
```

### Ejemplo con Supervisor (Linux)

```ini
[program:celery_worker]
command=/path/to/venv/bin/celery -A config worker --loglevel=info
directory=/path/to/django-importer
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/worker.log
```

## Alternativas a Redis

### RabbitMQ

```python
# settings.py
CELERY_BROKER_URL = 'amqp://guest:guest@localhost:5672//'
```

### Amazon SQS

```python
# settings.py
CELERY_BROKER_URL = 'sqs://'
# Requiere configuración adicional de AWS
```

### Base de Datos (no recomendado para producción)

```python
# settings.py
CELERY_BROKER_URL = 'django://'
# Requiere: pip install celery[django-db]
```

## Mejores Prácticas

1. **Desarrollo:** No uses Celery, procesa síncronamente
2. **Producción pequeña (< 1000 registros):** Opcional, puede funcionar sin Celery
3. **Producción grande (> 1000 registros):** **Usa Celery**
4. **Monitoreo:** Usa Flower para monitorear workers
   ```bash
   pip install flower
   celery -A config flower
   # Abre http://localhost:5555
   ```

## Recursos Adicionales

- [Documentación oficial de Celery](https://docs.celeryproject.org/)
- [Celery con Django](https://docs.celeryproject.org/en/stable/django/first-steps-with-django.html)
- [Redis Quick Start](https://redis.io/docs/getting-started/)

## Resumen

- ✅ **Opcional:** El sistema funciona sin Celery
- ✅ **Automático:** Detecta y usa Celery si está disponible
- ✅ **Escalable:** Procesa miles de registros sin problemas
- ✅ **Transparente:** Mismo código, funciona con o sin Celery
- ✅ **Monitoreable:** Auto-refresh y progreso en tiempo real
