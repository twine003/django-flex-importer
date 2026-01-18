@echo off
REM Script para ejecutar pruebas de Celery en Windows

echo ============================================================
echo PRUEBAS DE CELERY - DJANGO-FLEX-IMPORTER
echo ============================================================
echo.

REM Verificar si existe el entorno virtual
if exist venv\Scripts\activate.bat (
    echo [1/3] Activando entorno virtual...
    call venv\Scripts\activate.bat
) else (
    echo ERROR: No se encontro el entorno virtual en 'venv'
    echo.
    echo Crea uno con:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

echo [2/3] Verificando dependencias...
python -c "import django; import celery; import redis" 2>nul
if errorlevel 1 (
    echo.
    echo ERROR: Faltan dependencias. Instalando...
    pip install -q django celery redis
)

echo [3/3] Ejecutando pruebas...
echo.
python test_celery_async.py

echo.
echo ============================================================
echo.
pause
