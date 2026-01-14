@echo off
REM Script de configuración inicial para Windows

echo ===================================
echo Django FlexImporter - Setup
echo ===================================

REM Crear entorno virtual si no existe
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
)

REM Activar entorno virtual
echo Activando entorno virtual...
call venv\Scripts\activate.bat

REM Instalar dependencias
echo Instalando dependencias...
pip install -r requirements.txt

REM Ejecutar migraciones
echo Ejecutando migraciones...
python manage.py migrate

REM Crear superusuario
echo.
echo Crear superusuario para acceder al admin:
python manage.py createsuperuser

echo.
echo ===================================
echo Setup completado!
echo ===================================
echo.
echo Para iniciar el servidor, ejecuta:
echo   python manage.py runserver
echo.
echo Luego accede al admin en:
echo   http://localhost:8000/admin/
echo.
pause
