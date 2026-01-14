# Guía de Contribución

¡Gracias por tu interés en contribuir a django-flex-importer! 🎉

## Cómo Contribuir

### Reportar Bugs

Si encuentras un bug, por favor crea un [issue](https://github.com/yourusername/django-flex-importer/issues) incluyendo:

1. **Descripción clara del problema**
2. **Pasos para reproducir** el bug
3. **Comportamiento esperado** vs comportamiento actual
4. **Versión de Django** y **Python** que estás usando
5. **Código de ejemplo** si es posible

### Sugerir Mejoras

Las sugerencias son bienvenidas. Abre un issue con:

1. **Descripción de la mejora**
2. **Casos de uso** donde sería útil
3. **Ejemplo de cómo se usaría** (API propuesta)

### Pull Requests

1. **Fork** el repositorio
2. **Crea una rama** para tu feature: `git checkout -b feature/nueva-funcionalidad`
3. **Escribe código** siguiendo el estilo del proyecto
4. **Agrega tests** si es posible
5. **Actualiza documentación** si es necesario
6. **Commit** con mensajes descriptivos
7. **Push** a tu fork: `git push origin feature/nueva-funcionalidad`
8. **Abre un Pull Request** describiendo tus cambios

## Configuración del Entorno de Desarrollo

### 1. Clonar el repositorio

```bash
git clone https://github.com/yourusername/django-flex-importer.git
cd django-flex-importer
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias de desarrollo

```bash
pip install -e ".[dev]"
```

Esto instala el paquete en modo editable junto con las dependencias de desarrollo (pytest, black, flake8, etc.)

### 4. Ejecutar migraciones

```bash
python manage.py migrate
```

### 5. Crear superusuario

```bash
python manage.py createsuperuser
```

### 6. Ejecutar el servidor

```bash
python manage.py runserver
```

## Estándares de Código

### Formato de Código

Usamos **Black** para formateo automático:

```bash
black flex_importer/
```

### Linting

Usamos **flake8** para verificar el código:

```bash
flake8 flex_importer/
```

### Orden de Imports

Usamos **isort** para ordenar imports:

```bash
isort flex_importer/
```

### Ejecutar todos los checks

```bash
black flex_importer/
isort flex_importer/
flake8 flex_importer/
```

## Testing

### Ejecutar tests

```bash
pytest
```

### Con coverage

```bash
pytest --cov=flex_importer --cov-report=html
```

### Escribir tests

Los tests van en `tests/`. Ejemplo:

```python
import pytest
from django.test import TestCase
from flex_importer.base import FlexImporter


class MyTest(TestCase):
    def test_something(self):
        # Tu test aquí
        assert True
```

## Estructura del Proyecto

```
django-flex-importer/
├── flex_importer/          # Código principal del paquete
│   ├── base.py            # FlexImporter base
│   ├── model_importer.py  # FlexModelImporter
│   ├── models.py          # ImportLog model
│   ├── admin.py           # Django admin
│   ├── processor.py       # Import processor
│   ├── tasks.py           # Celery tasks
│   ├── utils.py           # Utilities
│   ├── registry.py        # Importer registry
│   └── templates/         # Admin templates
├── tests/                 # Tests del paquete
├── example_app/           # App de ejemplo (no se distribuye)
├── docs/                  # Documentación adicional
├── setup.py               # Setup tradicional
├── pyproject.toml         # Setup moderno
└── README.md              # Documentación principal
```

## Convenciones de Código

### Docstrings

Usa docstrings en formato Google:

```python
def my_function(param1, param2):
    """
    Descripción breve de la función.

    Args:
        param1 (str): Descripción del parámetro 1
        param2 (int): Descripción del parámetro 2

    Returns:
        bool: True si exitoso, False en caso contrario

    Raises:
        ValueError: Si param2 es negativo
    """
    pass
```

### Mensajes de Commit

Usa mensajes claros y descriptivos:

```bash
# ✅ Bueno
git commit -m "Add support for decimal fields in FlexModelImporter"
git commit -m "Fix duplicate imports when using key_field"
git commit -m "Update README with Celery configuration"

# ❌ Malo
git commit -m "fix bug"
git commit -m "update"
git commit -m "changes"
```

### Nomenclatura

- **Clases**: `PascalCase` (ej: `FlexImporter`)
- **Funciones/Métodos**: `snake_case` (ej: `import_action`)
- **Constantes**: `UPPER_SNAKE_CASE` (ej: `DEFAULT_TIMEOUT`)
- **Variables privadas**: `_leading_underscore` (ej: `_internal_method`)

## Áreas donde Contribuir

### 🐛 Bugs Conocidos

Revisa los [issues](https://github.com/yourusername/django-flex-importer/issues) etiquetados como `bug`.

### ✨ Features Deseados

Algunos features que serían útiles:

1. **Soporte para más formatos**: XML, Parquet, etc.
2. **Validación avanzada**: Integración con Django validators
3. **Transformaciones**: Hooks para transformar datos antes de importar
4. **Importación parcial**: Importar solo filas específicas
5. **Rollback**: Deshacer importaciones
6. **Dry-run mode**: Validar sin importar
7. **Webhooks**: Notificaciones cuando termina una importación
8. **API REST**: Endpoints para importar vía API
9. **Internacionalización**: Traducciones a otros idiomas
10. **Más tests**: Aumentar cobertura de tests

### 📖 Documentación

La documentación siempre puede mejorar:

- Más ejemplos de uso
- Tutoriales en video
- Casos de uso comunes
- Traducciones

### 🧪 Testing

- Escribir más tests
- Tests de integración
- Tests de performance
- Tests para diferentes versiones de Django

## Proceso de Review

1. **Automated checks**: GitHub Actions ejecuta tests automáticamente
2. **Code review**: Un mantenedor revisará tu código
3. **Cambios solicitados**: Puede que se soliciten cambios
4. **Merge**: Una vez aprobado, se hace merge a `main`

## Versioning

Seguimos [Semantic Versioning](https://semver.org/):

- **MAJOR**: Cambios incompatibles en la API
- **MINOR**: Nuevas funcionalidades compatible hacia atrás
- **PATCH**: Bug fixes compatibles hacia atrás

## Licencia

Al contribuir, aceptas que tu código se distribuirá bajo la [Licencia MIT](LICENSE).

## Código de Conducta

### Nuestro Compromiso

Este proyecto se compromete a proporcionar un ambiente amigable, seguro y acogedor para todos.

### Comportamiento Esperado

- Ser respetuoso con diferentes puntos de vista
- Aceptar críticas constructivas
- Enfocarse en lo mejor para la comunidad
- Mostrar empatía hacia otros miembros

### Comportamiento Inaceptable

- Comentarios ofensivos o discriminatorios
- Ataques personales o políticos
- Acoso público o privado
- Publicar información privada de otros sin permiso

## Preguntas

Si tienes preguntas, puedes:

1. Abrir un [issue](https://github.com/yourusername/django-flex-importer/issues)
2. Iniciar una [discussion](https://github.com/yourusername/django-flex-importer/discussions)
3. Contactar a los mantenedores

## Agradecimientos

¡Gracias por contribuir al proyecto! 🙏

Cada contribución, grande o pequeña, es valiosa y apreciada.
