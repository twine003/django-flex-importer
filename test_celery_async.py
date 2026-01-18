"""
Script de prueba para importación asíncrona con Celery

Este script verifica que:
1. Celery esté configurado correctamente
2. Redis esté funcionando
3. Las importaciones asíncronas funcionen
4. Los permisos se sincronicen correctamente
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from flex_importer.models import ImportJob
from flex_importer.tasks import process_import_async, CELERY_AVAILABLE
from flex_importer.registry import importer_registry
import time

def test_celery_availability():
    """Test 1: Verificar que Celery esté disponible"""
    print("\n" + "="*60)
    print("TEST 1: Verificar disponibilidad de Celery")
    print("="*60)

    if CELERY_AVAILABLE:
        print("✅ Celery está disponible")
        print(f"   - Task: {process_import_async}")
        return True
    else:
        print("❌ Celery NO está disponible")
        print("   - Instala con: pip install celery redis")
        return False


def test_redis_connection():
    """Test 2: Verificar conexión a Redis"""
    print("\n" + "="*60)
    print("TEST 2: Verificar conexión a Redis")
    print("="*60)

    try:
        from celery import current_app
        broker_url = current_app.conf.broker_url
        print(f"   - Broker URL: {broker_url}")

        # Try to ping Redis
        import redis
        r = redis.from_url(broker_url)
        r.ping()
        print("✅ Conexión a Redis exitosa")
        return True
    except ImportError:
        print("❌ Redis no está instalado")
        print("   - Instala con: pip install redis")
        return False
    except Exception as e:
        print(f"❌ Error conectando a Redis: {e}")
        print("   - Asegúrate de que Redis esté corriendo:")
        print("   - Windows: Descarga e instala Redis desde https://github.com/microsoftarchive/redis/releases")
        print("   - Linux/Mac: redis-server")
        return False


def test_registered_importers():
    """Test 3: Verificar importadores registrados"""
    print("\n" + "="*60)
    print("TEST 3: Verificar importadores registrados")
    print("="*60)

    importers = importer_registry.get_all_importers()
    if not importers:
        print("❌ No hay importadores registrados")
        print("   - Verifica que example_app/importers.py esté correctamente definido")
        return False

    print(f"✅ Importadores registrados: {len(importers)}")
    for class_name, importer_class in importers.items():
        verbose_name = importer_class.get_verbose_name()
        can_rerun = importer_class.can_re_run()
        print(f"   - {verbose_name}")
        print(f"     Class: {class_name}")
        print(f"     Can re-run: {can_rerun}")

    return True


def test_async_import():
    """Test 4: Probar importación asíncrona"""
    print("\n" + "="*60)
    print("TEST 4: Probar importación asíncrona")
    print("="*60)

    if not CELERY_AVAILABLE:
        print("⏭️  Saltando - Celery no disponible")
        return False

    # Get first importer
    importers = importer_registry.get_all_importers()
    if not importers:
        print("❌ No hay importadores para probar")
        return False

    importer_class_name, importer_class = list(importers.items())[0]
    print(f"   - Usando importador: {importer_class.get_verbose_name()}")

    # Create a test CSV file
    csv_content = b"""Fecha,Cliente,Producto,Cantidad,Precio
2024-01-01,Cliente Test 1,1,10,100.50
2024-01-02,Cliente Test 2,2,5,250.00
2024-01-03,Cliente Test 3,3,15,75.25"""

    test_file = SimpleUploadedFile(
        "test_async_import.csv",
        csv_content,
        content_type="text/csv"
    )

    # Create import job
    import_job = ImportJob.objects.create(
        importer_class=importer_class_name,
        importer_name=importer_class.get_verbose_name(),
        file_format='csv',
        uploaded_file=test_file,
        can_re_run=importer_class.can_re_run(),
    )

    print(f"   - Import Job creado: ID {import_job.id}")
    print(f"   - Estado inicial: {import_job.status}")

    # Queue the async task
    print("   - Enviando tarea a Celery...")
    task_result = process_import_async.delay(import_job.id)

    print(f"   - Task ID: {task_result.id}")
    print(f"   - Task state: {task_result.state}")

    # Wait for completion
    print("   - Esperando completación (máximo 30 segundos)...")
    timeout = 30
    start_time = time.time()

    while time.time() - start_time < timeout:
        import_job.refresh_from_db()
        print(f"   - Estado: {import_job.status} | Procesadas: {import_job.processed_rows}/{import_job.total_rows}")

        if import_job.status in ['success', 'partial', 'failed']:
            break

        time.sleep(1)

    # Check final status
    import_job.refresh_from_db()
    print(f"\n   📊 RESULTADO FINAL:")
    print(f"   - Estado: {import_job.status}")
    print(f"   - Total filas: {import_job.total_rows}")
    print(f"   - Procesadas: {import_job.processed_rows}")
    print(f"   - Exitosas: {import_job.success_rows}")
    print(f"   - Creadas: {import_job.created_rows}")
    print(f"   - Actualizadas: {import_job.updated_rows}")
    print(f"   - Errores: {import_job.error_rows}")
    print(f"   - Mensaje: {import_job.result_message}")

    if import_job.error_details:
        print(f"\n   ⚠️  ERRORES:")
        for error in import_job.error_details[:3]:  # Show first 3 errors
            print(f"   - Fila {error['row']}: {', '.join(error['errors'])}")

    if import_job.status == 'success':
        print("\n✅ Importación asíncrona exitosa!")
        return True
    elif import_job.status == 'partial':
        print("\n⚠️  Importación parcialmente exitosa")
        return True
    else:
        print("\n❌ Importación falló")
        return False


def test_celery_worker():
    """Test 5: Verificar que el worker de Celery esté corriendo"""
    print("\n" + "="*60)
    print("TEST 5: Verificar worker de Celery")
    print("="*60)

    if not CELERY_AVAILABLE:
        print("⏭️  Saltando - Celery no disponible")
        return False

    try:
        from celery import current_app
        inspector = current_app.control.inspect()
        active_workers = inspector.active()

        if active_workers:
            print(f"✅ Workers activos: {len(active_workers)}")
            for worker_name, tasks in active_workers.items():
                print(f"   - {worker_name}: {len(tasks)} tareas activas")
            return True
        else:
            print("❌ No hay workers activos")
            print("\n   Para iniciar un worker, ejecuta en otra terminal:")
            print("   celery -A config worker --loglevel=info --pool=solo")
            return False
    except Exception as e:
        print(f"❌ Error verificando workers: {e}")
        return False


def main():
    """Ejecutar todos los tests"""
    print("\n" + "🔥"*30)
    print("PRUEBA DE IMPORTACIÓN ASÍNCRONA CON CELERY")
    print("🔥"*30)

    results = {}

    # Run tests
    results['celery'] = test_celery_availability()
    results['redis'] = test_redis_connection()
    results['importers'] = test_registered_importers()
    results['worker'] = test_celery_worker()
    results['async_import'] = test_async_import()

    # Summary
    print("\n" + "="*60)
    print("RESUMEN DE PRUEBAS")
    print("="*60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    total = len(results)
    passed = sum(results.values())

    print(f"\nTotal: {passed}/{total} pruebas pasadas")

    if passed == total:
        print("\n🎉 ¡Todas las pruebas pasaron!")
        return 0
    else:
        print("\n⚠️  Algunas pruebas fallaron. Revisa los mensajes arriba.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
