# Django FlexImporter

[![PyPI version](https://badge.fury.io/py/django-flex-importer.svg)](https://badge.fury.io/py/django-flex-importer)
[![Python Version](https://img.shields.io/pypi/pyversions/django-flex-importer.svg)](https://pypi.org/project/django-flex-importer/)
[![Django Version](https://img.shields.io/badge/django-3.2%20%7C%204.0%20%7C%204.1%20%7C%204.2%20%7C%205.0-blue.svg)](https://www.djangoproject.com/)
[![CI](https://github.com/twine003/django-flex-importer/workflows/CI/badge.svg)](https://github.com/twine003/django-flex-importer/actions)
[![codecov](https://codecov.io/gh/twine003/django-flex-importer/branch/main/graph/badge.svg)](https://codecov.io/gh/twine003/django-flex-importer)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Sistema flexible de importación de datos para Django que permite crear importadores personalizados mediante herencia de clases, con soporte para múltiples formatos (XLSX, CSV, JSON) y validación automática de datos.

## 📚 Documentación

- **[Guía Rápida (QUICKSTART.md)](QUICKSTART.md)**: Crea un importador en menos de 10 líneas
- **[Demo Completa (DEMO.md)](DEMO.md)**: Walkthrough paso a paso con ejemplos
- **[Guía de key_field (KEY_FIELD_GUIDE.md)](KEY_FIELD_GUIDE.md)**: Actualización automática de registros existentes
- **[Configuración de Celery (CELERY_SETUP.md)](CELERY_SETUP.md)**: Importaciones asíncronas para miles de registros
- **[Solución de Problemas (TROUBLESHOOTING.md)](TROUBLESHOOTING.md)**: Problemas comunes y soluciones
- **Este README**: Documentación completa de referencia

## Características

- **Importadores Personalizables**: Define tus propios importadores heredando de `FlexImporter` o `FlexModelImporter`
- **Importadores desde Modelos**: Crea importadores automáticamente desde modelos Django
- **Actualización Inteligente**: Usa `key_field` para actualizar registros existentes en lugar de crear duplicados
- **Procesamiento Asíncrono**: Soporte opcional para Celery para importaciones de miles de registros
- **Múltiples Formatos**: Soporte para XLSX, CSV y JSON
- **Validación Automática**: Validación de tipos de datos y campos requeridos
- **Generación de Plantillas**: Descarga plantillas en cualquier formato soportado
- **Bitácora Completa**: Registro detallado de todas las importaciones con estadísticas de creados/actualizados
- **Re-ejecución**: Capacidad de re-ejecutar importaciones anteriores
- **Interfaz Admin**: Integración completa con Django Admin
- **Seguimiento en Tiempo Real**: Log de progreso y estadísticas de importación con auto-refresh

## Instalación

### Instalación desde PyPI (Recomendado)

```bash
pip install django-flex-importer
```

Para soporte asíncrono con Celery:

```bash
pip install django-flex-importer[async]
```

### Configuración

1. Agrega `flex_importer` a `INSTALLED_APPS` en `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'flex_importer',
    # ...
]
```

2. Ejecuta las migraciones:

```bash
python manage.py migrate flex_importer
```

3. (Opcional) Configurar Celery para procesamiento asíncrono:

```python
# settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

Ver [CELERY_SETUP.md](CELERY_SETUP.md) para más detalles.

### Instalación desde el código fuente

Si quieres contribuir o usar la última versión de desarrollo:

```bash
# 1. Clonar el repositorio
git clone https://github.com/twine003/django-flex-importer.git
cd django-flex-importer

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 3. Instalar en modo desarrollo
pip install -e ".[dev]"

# 4. Ejecutar migraciones
python manage.py migrate

# 5. Crear superusuario
python manage.py createsuperuser

# 6. Ejecutar servidor
python manage.py runserver
```

## Uso

Hay dos formas de crear importadores:

### 1. FlexModelImporter (Recomendado - Automático desde Modelo)

La forma más rápida es usar `FlexModelImporter` que automáticamente extrae los campos del modelo:

```python
from flex_importer.model_importer import FlexModelImporter
from .models import Sale


class SalesModelImporter(FlexModelImporter):
    """Importador automático desde el modelo Sale"""

    class Meta:
        model = Sale  # El modelo del cual extraer los campos
        verbose_name = "Importador de Ventas (desde Modelo)"
        can_re_run = True

        # Opcional: excluir campos específicos
        # exclude_fields = ['some_field']

        # Opcional: incluir solo campos específicos
        # include_fields = ['date', 'cliente', 'producto', 'cantidad', 'precio']

    def import_action(self, row_data):
        """
        Implementa la lógica de importación.

        Args:
            row_data (dict): Datos validados de la fila

        Returns:
            bool or str: True si es exitoso, mensaje de error si falla
        """
        try:
            # Valores por defecto para campos opcionales
            if row_data.get('cantidad') is None:
                row_data['cantidad'] = 1

            # Usar el helper para crear la instancia
            sale = self.create_instance(row_data)

            return True

        except Exception as e:
            return f"Error: {str(e)}"
```

**Ventajas de FlexModelImporter:**
- ✅ No necesitas definir los campos manualmente
- ✅ Automáticamente sincronizado con el modelo
- ✅ Menos código y más mantenible
- ✅ Incluye métodos helper: `create_instance()` y `update_or_create_instance()`

### 2. FlexImporter (Manual - Mayor Control)

Si necesitas mayor control sobre los campos, usa `FlexImporter`:

Crea un archivo `importers.py` en tu app de Django y define tu importador:

```python
from django.db import models
from flex_importer.base import FlexImporter
from .models import Sale


class SalesImporter(FlexImporter):
    """Importador de ventas"""

    # Define los campos usando tipos de Django
    date = models.DateTimeField(verbose_name='Fecha de Venta')
    cliente = models.TextField(verbose_name='Nombre del Cliente')
    producto = models.IntegerField(verbose_name='ID del Producto')
    cantidad = models.IntegerField(verbose_name='Cantidad', blank=True)
    precio = models.DecimalField(
        verbose_name='Precio Unitario',
        max_digits=10,
        decimal_places=2
    )

    class Meta:
        verbose_name = "Importador de Ventas"
        can_re_run = True  # Permite re-ejecutar importaciones

    def import_action(self, row_data):
        """
        Implementa la lógica de importación.

        Args:
            row_data (dict): Datos validados de la fila

        Returns:
            bool or str: True si es exitoso, mensaje de error si falla
        """
        try:
            # Valor por defecto para campos opcionales
            if row_data.get('cantidad') is None:
                row_data['cantidad'] = 1

            # Crear el objeto
            sale = Sale.objects.create(
                date=row_data['date'],
                cliente=row_data['cliente'],
                producto=row_data['producto'],
                cantidad=row_data['cantidad'],
                precio=row_data['precio']
            )

            return True

        except Exception as e:
            return f"Error al crear venta: {str(e)}"
```

### 3. Métodos Helper de FlexModelImporter

`FlexModelImporter` incluye métodos útiles para facilitar la importación:

#### `create_instance(validated_data)`
Crea una nueva instancia del modelo:

```python
def import_action(self, row_data):
    sale = self.create_instance(row_data)
    return True
```

#### `update_or_create_instance(lookup_fields, validated_data)`
Actualiza o crea una instancia basándose en campos de búsqueda:

```python
def import_action(self, row_data):
    # Buscar por 'producto' y actualizar o crear
    lookup = {'producto': row_data.pop('producto')}
    sale, created = self.update_or_create_instance(lookup, row_data)

    if created:
        return True
    else:
        return "Registro actualizado"
```

### 4. Tipos de Campos Soportados

El sistema soporta los siguientes tipos de campos de Django:

- `CharField` / `TextField`: Texto
- `IntegerField`: Números enteros
- `FloatField`: Números decimales
- `DecimalField`: Decimales precisos
- `BooleanField`: Booleanos (true/false, yes/no, si/no, 1/0)
- `DateField`: Fechas (formato: YYYY-MM-DD)
- `DateTimeField`: Fechas con hora (formato ISO)
- `EmailField`: Correos electrónicos
- `ForeignKey`: Acepta el ID del objeto relacionado

### 5. Configuración Meta

La clase `Meta` del importador soporta las siguientes opciones:

**Para FlexImporter y FlexModelImporter:**
- `verbose_name`: Nombre que aparecerá en el selector del admin
- `can_re_run`: Si `True`, permite re-ejecutar importaciones anteriores

**Adicionales para FlexModelImporter:**
- `model`: El modelo Django del cual extraer los campos (requerido)
- `exclude_fields`: Lista de campos a excluir (opcional)
- `include_fields`: Lista de campos a incluir (si se especifica, solo se incluyen estos campos)

### 6. Usar el Importador

#### Desde el Django Admin:

1. Ve a "Bitácoras de Importación" en el admin
2. Haz clic en "Nueva Importación"
3. Selecciona tu importador del dropdown
4. Descarga la plantilla en el formato deseado (XLSX, CSV o JSON)
5. Llena la plantilla con tus datos
6. Selecciona el formato del archivo
7. Sube el archivo completado
8. Haz clic en "Importar"

#### Estructura de las Plantillas:

**XLSX/CSV:**
- La primera fila contiene los encabezados (nombres de los campos)
- Los campos requeridos se marcan con asterisco (*)
- Las filas siguientes contienen los datos

**JSON:**
```json
{
  "template_info": {
    "importer": "Importador de Ventas",
    "fields": [
      {
        "name": "date",
        "verbose_name": "Fecha de Venta",
        "type": "datetime",
        "required": true
      },
      ...
    ]
  },
  "data": [
    {
      "date": "2024-01-15T10:30:00",
      "cliente": "Juan Pérez",
      "producto": 101,
      "cantidad": 5,
      "precio": "29.99"
    }
  ]
}
```

### 7. Bitácora de Importaciones

Cada importación se registra con:

- **Estado**: Pendiente, Procesando, Exitoso, Parcial, Fallido
- **Estadísticas**: Total de filas, procesadas, exitosas, con error
- **Tasa de Éxito**: Porcentaje de filas importadas correctamente
- **Detalles de Errores**: Información específica sobre cada error
- **Log de Progreso**: Registro cronológico de la importación
- **Archivo Original**: El archivo importado se guarda para referencia
- **Duración**: Tiempo que tomó la importación

### 8. Re-ejecutar Importaciones

Si un importador tiene `can_re_run = True`:

1. Ve al detalle de una importación en el admin
2. Haz clic en el botón "Re-ejecutar"
3. Se creará una nueva importación usando el mismo archivo

## Procesamiento Asíncrono con Celery

Para importaciones con **miles de registros**, el sistema soporta procesamiento asíncrono usando Celery.

### ¿Cuándo usar Celery?

- **Sin Celery (síncrono)**: Funciona bien para cientos de registros
- **Con Celery (asíncrono)**: Recomendado para miles de registros

### Características del modo asíncrono:

- ✅ **Detección automática**: El sistema detecta si Celery está disponible
- ✅ **Respuesta inmediata**: No hay que esperar a que termine la importación
- ✅ **Auto-refresh**: La página de detalle se actualiza automáticamente cada 5 segundos
- ✅ **Monitoreo en tiempo real**: Ve el progreso mientras se procesa
- ✅ **Sin cambios en el código**: Tus importadores funcionan igual con o sin Celery

### Configuración rápida:

```bash
# 1. Instalar Celery y Redis
pip install celery redis

# 2. Iniciar Redis
redis-server

# 3. Configurar en settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# 4. Iniciar worker de Celery
celery -A config worker --loglevel=info
```

**Para más detalles**: Ver [CELERY_SETUP.md](CELERY_SETUP.md)

## Sistema de Permisos

El sistema genera automáticamente permisos de Django para cada importador registrado, permitiendo control granular de acceso a nivel de usuario o grupo.

### Características:

- ✅ **Auto-generación**: Los permisos se crean automáticamente al ejecutar `migrate`
- ✅ **Limpieza automática**: Los permisos se eliminan cuando se elimina un importador
- ✅ **Integración con Django**: Compatible con usuarios, grupos y el sistema de permisos estándar
- ✅ **Filtrado en Admin**: Los usuarios solo ven los importadores que tienen permitidos
- ✅ **Superusuarios**: Los superusuarios tienen acceso a todos los importadores

### Funcionamiento:

Cuando registras un importador, el sistema automáticamente crea un permiso con el formato:

```
can_use_<nombre_importador_en_minusculas>
```

Por ejemplo, si tienes un `SalesImporter`, el permiso será: `can_use_salesimporter`

### Asignar permisos a un usuario:

```python
from django.contrib.auth.models import User, Permission

# Obtener el usuario
user = User.objects.get(username='john')

# Obtener el permiso
permission = Permission.objects.get(codename='can_use_salesimporter')

# Asignar el permiso
user.user_permissions.add(permission)
```

### Asignar permisos a un grupo:

```python
from django.contrib.auth.models import Group, Permission

# Crear o obtener el grupo
group = Group.objects.get_or_create(name='Sales Team')[0]

# Obtener el permiso
permission = Permission.objects.get(codename='can_use_salesimporter')

# Asignar el permiso al grupo
group.permissions.add(permission)

# Agregar usuario al grupo
user.groups.add(group)
```

### Sincronizar permisos manualmente:

Si necesitas sincronizar los permisos manualmente (por ejemplo, después de agregar nuevos importadores):

```bash
python manage.py sync_importer_permissions
```

Con la opción `--dry-run` para ver qué cambios se harían sin aplicarlos:

```bash
python manage.py sync_importer_permissions --dry-run
```

### Comportamiento en el Admin:

- Los usuarios **con permiso** verán el importador en el dropdown de selección
- Los usuarios **sin permiso** NO verán el importador
- Los **superusuarios** siempre ven todos los importadores
- Si un usuario intenta acceder a un importador sin permiso, se muestra un mensaje de error

## Estructura del Proyecto

```
django-importer/
├── config/                  # Configuración de Django
│   ├── settings.py
│   ├── celery.py           # Configuración de Celery (opcional)
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── flex_importer/          # App principal de importación
│   ├── base.py            # Clase base FlexImporter
│   ├── model_importer.py  # Clase FlexModelImporter
│   ├── models.py          # Modelo ImportJob
│   ├── admin.py           # Admin personalizado
│   ├── processor.py       # Procesador de importaciones
│   ├── tasks.py           # Tareas de Celery (async)
│   ├── utils.py           # Utilidades (detección de Celery)
│   ├── registry.py        # Registro de importadores
│   └── templates/         # Templates del admin
├── example_app/           # App de ejemplo
│   ├── models.py         # Modelo Sale
│   ├── admin.py          # Admin de Sale
│   └── importers.py      # Importadores de ejemplo
├── media/                # Archivos subidos
├── manage.py
└── requirements.txt
```

## Validación de Datos

El sistema valida automáticamente:

1. **Campos Requeridos**: Verifica que los campos obligatorios estén presentes
2. **Tipos de Datos**: Convierte y valida los tipos de datos
3. **Formato**: Valida formatos específicos (fechas, emails, etc.)

Los errores de validación se registran en la bitácora con:
- Número de fila
- Campo con error
- Mensaje de error detallado
- Datos de la fila

## Ejemplo Completo

Ver [example_app/importers.py](example_app/importers.py) para ejemplos completos de importadores.

El proyecto incluye tres importadores de ejemplo:

1. **SalesImporter**: Importa ventas usando FlexImporter (definición manual de campos)
2. **SalesModelImporter**: Importa ventas usando FlexModelImporter (automático desde modelo)
3. **ProductImporter**: Importa productos y no puede ser re-ejecutado

## Tecnologías

- Django 3.2+
- Python 3.7+
- openpyxl (para archivos Excel)
- SQLite (puede cambiarse a PostgreSQL, MySQL, etc.)

## Licencia

MIT

## Autor

Desarrollado para demostrar un sistema flexible de importación en Django.
