#!/bin/bash
# Script de configuración inicial

echo "==================================="
echo "Django FlexImporter - Setup"
echo "==================================="

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python -m venv venv
fi

# Activar entorno virtual
echo "Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias
echo "Instalando dependencias..."
pip install -r requirements.txt

# Ejecutar migraciones
echo "Ejecutando migraciones..."
python manage.py migrate

# Crear superusuario
echo ""
echo "Crear superusuario para acceder al admin:"
python manage.py createsuperuser

echo ""
echo "==================================="
echo "Setup completado!"
echo "==================================="
echo ""
echo "Para iniciar el servidor, ejecuta:"
echo "  python manage.py runserver"
echo ""
echo "Luego accede al admin en:"
echo "  http://localhost:8000/admin/"
echo ""
