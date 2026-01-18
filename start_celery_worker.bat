@echo off
REM Script para iniciar el worker de Celery en Windows

echo ============================================================
echo INICIANDO CELERY WORKER
echo ============================================================
echo.

REM Verificar si existe el entorno virtual
if exist venv\Scripts\activate.bat (
    echo [*] Activando entorno virtual...
    call venv\Scripts\activate.bat
) else (
    echo ERROR: No se encontro el entorno virtual en 'venv'
    pause
    exit /b 1
)

echo [*] Verificando Celery...
python -c "import celery" 2>nul
if errorlevel 1 (
    echo ERROR: Celery no esta instalado
    echo Instalando Celery y Redis...
    pip install celery redis
)

echo [*] Verificando Redis...
redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo.
    echo ============================================================
    echo ATENCION: Redis no esta corriendo!
    echo ============================================================
    echo.
    echo Para Windows, tienes estas opciones:
    echo.
    echo 1. Usar Docker:
    echo    docker run -d -p 6379:6379 redis:latest
    echo.
    echo 2. Descargar Memurai (Redis for Windows):
    echo    https://www.memurai.com/get-memurai
    echo.
    echo 3. Usar WSL2:
    echo    wsl
    echo    sudo service redis-server start
    echo.
    echo Presiona cualquier tecla una vez que Redis este corriendo...
    pause >nul
)

echo.
echo ============================================================
echo WORKER INICIADO
echo ============================================================
echo.
echo El worker de Celery esta corriendo.
echo Deja esta ventana abierta mientras usas las importaciones.
echo.
echo Presiona Ctrl+C para detener el worker.
echo ============================================================
echo.

celery -A config worker --loglevel=info --pool=solo
