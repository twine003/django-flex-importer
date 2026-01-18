# Guía de Pruebas de Celery

Esta guía te ayudará a probar las importaciones asíncronas con Celery.

## Requisitos Previos

### 1. Instalar dependencias

```bash
pip install celery redis
```

### 2. Instalar y ejecutar Redis

#### Windows:
```bash
# Opción 1: Usar Memurai (Redis for Windows)
# Descargar desde: https://www.memurai.com/get-memurai

# Opción 2: Usar Docker
docker run -d -p 6379:6379 redis:latest

# Opción 3: Usar WSL2
wsl
sudo apt-get update
sudo apt-get install redis-server
redis-server
```

#### Linux/Mac:
```bash
# Instalar Redis
sudo apt-get install redis-server  # Ubuntu/Debian
brew install redis                  # macOS

# Iniciar Redis
redis-server
```

### 3. Verificar que Redis esté corriendo

```bash
redis-cli ping
# Debe responder: PONG
```

## Ejecutar las Pruebas

### Paso 1: Iniciar el worker de Celery

Abre una **nueva terminal** y ejecuta:

```bash
# Windows
celery -A config worker --loglevel=info --pool=solo

# Linux/Mac
celery -A config worker --loglevel=info
```

Deberías ver algo como:
```
-------------- celery@tu-computadora v5.x.x
---- **** -----
--- * ***  * -- Windows-10.0.19045-SP0
-- * - **** ---
- ** ---------- [config]
- ** ---------- .> app:         django_importer:0x...
- ** ---------- .> transport:   redis://localhost:6379/0
- ** ---------- .> results:     redis://localhost:6379/0
- *** --- * --- .> concurrency: 4 (solo)
-- ******* ----
--- ***** ----- [queues]
 -------------- .> celery           exchange=celery(direct) key=celery

[tasks]
  . flex_importer.process_import
```

### Paso 2: Ejecutar el script de pruebas

En otra terminal:

```bash
python test_celery_async.py
```

## Qué Verifica el Script de Pruebas

### Test 1: Disponibilidad de Celery
- ✅ Verifica que Celery esté instalado
- ✅ Verifica que el task esté registrado

### Test 2: Conexión a Redis
- ✅ Verifica que Redis esté corriendo
- ✅ Verifica que la conexión funcione

### Test 3: Importadores Registrados
- ✅ Verifica que hay importadores disponibles
- ✅ Lista todos los importadores con sus propiedades

### Test 4: Worker de Celery
- ✅ Verifica que el worker esté corriendo
- ✅ Lista workers activos

### Test 5: Importación Asíncrona
- ✅ Crea un archivo CSV de prueba
- ✅ Crea un ImportJob
- ✅ Envía la tarea a Celery
- ✅ Monitorea el progreso
- ✅ Verifica el resultado final

## Salida Esperada

Si todo funciona correctamente, deberías ver:

```
🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥
PRUEBA DE IMPORTACIÓN ASÍNCRONA CON CELERY
🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥

============================================================
TEST 1: Verificar disponibilidad de Celery
============================================================
✅ Celery está disponible
   - Task: <@task: flex_importer.process_import ...>

============================================================
TEST 2: Verificar conexión a Redis
============================================================
   - Broker URL: redis://localhost:6379/0
✅ Conexión a Redis exitosa

============================================================
TEST 3: Verificar importadores registrados
============================================================
✅ Importadores registrados: 3
   - Importador de Ventas (Automático)
     Class: example_app.importers.SalesModelImporter
     Can re-run: True
   - Importador de Ventas (Manual)
     Class: example_app.importers.SalesImporter
     Can re-run: True
   - Importador de Productos
     Class: example_app.importers.ProductImporter
     Can re-run: False

============================================================
TEST 4: Verificar worker de Celery
============================================================
✅ Workers activos: 1
   - celery@tu-computadora: 0 tareas activas

============================================================
TEST 5: Probar importación asíncrona
============================================================
   - Usando importador: Importador de Ventas (Automático)
   - Import Job creado: ID 1
   - Estado inicial: pending
   - Enviando tarea a Celery...
   - Task ID: abc123-def456-...
   - Task state: PENDING
   - Esperando completación (máximo 30 segundos)...
   - Estado: processing | Procesadas: 0/3
   - Estado: processing | Procesadas: 1/3
   - Estado: processing | Procesadas: 2/3
   - Estado: processing | Procesadas: 3/3
   - Estado: success | Procesadas: 3/3

   📊 RESULTADO FINAL:
   - Estado: success
   - Total filas: 3
   - Procesadas: 3
   - Exitosas: 3
   - Creadas: 3
   - Actualizadas: 0
   - Errores: 0
   - Mensaje: Importación completada exitosamente. 3 filas procesadas (3 creadas, 0 actualizadas).

✅ Importación asíncrona exitosa!

============================================================
RESUMEN DE PRUEBAS
============================================================
✅ PASS - celery
✅ PASS - redis
✅ PASS - importers
✅ PASS - worker
✅ PASS - async_import

Total: 5/5 pruebas pasadas

🎉 ¡Todas las pruebas pasaron!
```

## Solución de Problemas

### Problema: "Celery NO está disponible"

**Solución:**
```bash
pip install celery redis
```

### Problema: "Error conectando a Redis"

**Solución:**
1. Verifica que Redis esté corriendo:
   ```bash
   redis-cli ping
   ```
2. Si no responde, inicia Redis:
   ```bash
   redis-server
   ```

### Problema: "No hay workers activos"

**Solución:**
Abre una nueva terminal y ejecuta:
```bash
celery -A config worker --loglevel=info --pool=solo
```

### Problema: "Importación falló"

**Solución:**
1. Revisa los logs del worker de Celery
2. Verifica que el importador esté correctamente configurado
3. Revisa los errores detallados en `import_job.error_details`

### Problema: ImportError en Windows

**Solución:**
Usa `--pool=solo` al iniciar el worker:
```bash
celery -A config worker --loglevel=info --pool=solo
```

## Verificar en el Admin de Django

Después de ejecutar las pruebas, puedes ver el resultado en el admin:

```bash
python manage.py runserver
```

Ve a: http://localhost:8000/admin/flex_importer/importjob/

Deberías ver el ImportJob creado por el test con todos los detalles de la ejecución.

## Prueba Manual en el Admin

1. Ve a: http://localhost:8000/admin/
2. Click en "Trabajos de Importación" → "Nueva Importación"
3. Selecciona un importador
4. Sube un archivo
5. Verás un mensaje: "Importación iniciada en segundo plano"
6. La página se auto-refrescará cada 5 segundos mostrando el progreso

## Comandos Útiles

### Ver tareas en Redis
```bash
redis-cli
> KEYS *
```

### Monitorear Redis en tiempo real
```bash
redis-cli MONITOR
```

### Ver logs del worker con más detalle
```bash
celery -A config worker --loglevel=debug --pool=solo
```

### Purgar todas las tareas pendientes
```bash
celery -A config purge
```

## Siguiente Paso

Una vez que todas las pruebas pasen, estás listo para usar importaciones asíncronas en producción. Asegúrate de:

1. ✅ Configurar un broker de producción (Redis Cloud, RabbitMQ, etc.)
2. ✅ Configurar un supervisor para mantener el worker corriendo (systemd, supervisord, etc.)
3. ✅ Configurar monitoreo (Flower, Celery Inspect, etc.)
4. ✅ Ajustar la configuración de Celery según tus necesidades (timeouts, retries, etc.)
