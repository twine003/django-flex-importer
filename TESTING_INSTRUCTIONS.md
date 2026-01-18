# 🧪 Instrucciones para Probar Importaciones Asíncronas con Celery

Esta guía te mostrará cómo probar que las importaciones asíncronas con Celery funcionan correctamente en tu proyecto `django-flex-importer`.

## 📋 Archivos Creados

He creado estos archivos para facilitar las pruebas:

1. **`test_celery_async.py`**: Script automatizado de pruebas
2. **`CELERY_TEST.md`**: Guía detallada de troubleshooting
3. **`start_celery_worker.bat`**: Script para iniciar el worker (Windows)
4. **`run_celery_tests.bat`**: Script para ejecutar las pruebas (Windows)

## 🚀 Inicio Rápido (3 Pasos)

### Paso 1: Instalar Redis

#### Opción A - Docker (Recomendado):
```bash
docker run -d -p 6379:6379 --name redis-flex-importer redis:latest
```

#### Opción B - Memurai (Redis para Windows):
1. Descarga desde: https://www.memurai.com/get-memurai
2. Instala y ejecuta

#### Opción C - WSL2:
```bash
wsl
sudo service redis-server start
```

Verifica que Redis esté corriendo:
```bash
redis-cli ping
# Debe responder: PONG
```

### Paso 2: Instalar dependencias

```bash
# Activar entorno virtual
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Instalar Celery y Redis
pip install celery redis
```

### Paso 3: Ejecutar las pruebas

#### Ventana 1 - Iniciar el Worker:
```bash
# Windows
start_celery_worker.bat

# Linux/Mac
celery -A config worker --loglevel=info
```

#### Ventana 2 - Ejecutar Pruebas:
```bash
# Windows
run_celery_tests.bat

# Linux/Mac
python test_celery_async.py
```

## ✅ Resultado Esperado

Si todo funciona correctamente, verás:

```
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

## 🔍 Qué Prueba Cada Test

### ✅ Test 1: Disponibilidad de Celery
- Verifica que Celery esté instalado
- Verifica que el decorator `@shared_task` funcione
- Confirma que `process_import_async` esté disponible

### ✅ Test 2: Conexión a Redis
- Verifica que Redis esté corriendo
- Prueba la conexión al broker
- Verifica la URL de configuración

### ✅ Test 3: Importadores Registrados
- Lista todos los importadores disponibles
- Muestra sus propiedades (can_re_run, verbose_name, etc.)
- Confirma que el registry funciona

### ✅ Test 4: Worker de Celery
- Verifica que haya al menos un worker activo
- Muestra información de los workers
- Confirma que pueden recibir tareas

### ✅ Test 5: Importación Asíncrona Completa
- Crea un archivo CSV de prueba con 3 filas
- Crea un ImportJob
- Envía la tarea a Celery (`.delay()`)
- Monitorea el progreso en tiempo real
- Verifica el resultado final (success/partial/failed)
- Muestra estadísticas completas

## 🔧 Verificar Manualmente en el Admin

Después de que las pruebas pasen:

```bash
python manage.py runserver
```

1. Ve a: http://localhost:8000/admin/
2. Login con tu superusuario
3. Click en "Trabajos de Importación" → "Nueva Importación"
4. Selecciona un importador
5. Sube un archivo CSV/XLSX/JSON
6. Verás: "Importación iniciada en segundo plano"
7. La página se auto-refrescará cada 5 segundos
8. Podrás ver el progreso en tiempo real

## 📊 Monitorear Celery en Tiempo Real

### Ver tareas en el worker:
```bash
celery -A config inspect active
```

### Ver tareas programadas:
```bash
celery -A config inspect scheduled
```

### Ver estadísticas:
```bash
celery -A config inspect stats
```

### Purgar todas las tareas:
```bash
celery -A config purge
```

## ❌ Solución de Problemas

### Problema 1: "Celery NO está disponible"
```bash
pip install celery redis
```

### Problema 2: "Error conectando a Redis"
```bash
# Verifica que Redis esté corriendo
redis-cli ping

# Si no responde, inicia Redis
docker start redis-flex-importer
# o
redis-server
```

### Problema 3: "No hay workers activos"
```bash
# Abre una nueva terminal
celery -A config worker --loglevel=info --pool=solo
```

### Problema 4: "ImportError: DLL load failed" (Windows)
Usa `--pool=solo`:
```bash
celery -A config worker --loglevel=info --pool=solo
```

### Problema 5: Las tareas no se procesan
1. Verifica los logs del worker
2. Revisa que Redis esté en la misma URL (`redis://localhost:6379/0`)
3. Reinicia el worker

## 📝 Configuración Actual

La configuración de Celery está en `config/settings.py`:

```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
```

## 🎯 Próximos Pasos

Una vez que todas las pruebas pasen:

1. ✅ Prueba con archivos más grandes (100+ filas)
2. ✅ Prueba con diferentes formatos (CSV, XLSX, JSON)
3. ✅ Prueba el sistema de permisos
4. ✅ Prueba la re-ejecución de importaciones
5. ✅ Considera configurar Flower para monitoring:
   ```bash
   pip install flower
   celery -A config flower
   # Ve a: http://localhost:5555
   ```

## 📚 Documentación Adicional

- **CELERY_TEST.md**: Guía completa de troubleshooting
- **CELERY_SETUP.md**: Configuración detallada de Celery
- **README.md**: Documentación general del proyecto

## 🆘 ¿Necesitas Ayuda?

Si encuentras algún problema:

1. Revisa **CELERY_TEST.md** para soluciones detalladas
2. Verifica los logs del worker de Celery
3. Ejecuta las pruebas con `--loglevel=debug`
4. Revisa el ImportJob en el admin para ver errores detallados

---

¡Buena suerte con las pruebas! 🚀
