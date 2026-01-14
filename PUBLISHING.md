# Guía para Publicar en PyPI y GitHub

Esta guía te ayudará a subir el paquete `django-flex-importer` a PyPI y GitHub para que otros puedan instalarlo con `pip install`.

## Requisitos Previos

1. **Cuenta en GitHub**: https://github.com/signup
2. **Cuenta en PyPI**: https://pypi.org/account/register/
3. **Cuenta en TestPyPI** (opcional, para pruebas): https://test.pypi.org/account/register/

## Parte 1: Configurar el Proyecto Localmente

### 1. Actualizar Información Personal

Antes de publicar, actualiza los archivos con tu información:

**setup.py** (líneas 13-16):
```python
author='Tu Nombre',
author_email='tu.email@example.com',
url='https://github.com/tu-usuario/django-flex-importer',
```

**pyproject.toml** (línea 12):
```toml
authors = [
    {name = "Tu Nombre", email = "tu.email@example.com"}
]
```

**LICENSE** (línea 3):
```
Copyright (c) 2026 [Tu Nombre]
```

**CONTRIBUTING.md** - Reemplaza todas las URLs:
- `yourusername` → tu usuario de GitHub

### 2. Verificar que todo funciona

```bash
# Instalar dependencias de build
pip install build twine

# Crear el paquete
python -m build

# Verificar el paquete
twine check dist/*
```

Deberías ver:
```
Checking dist/django_flex_importer-1.0.0-py3-none-any.whl: PASSED
Checking dist/django-flex-importer-1.0.0.tar.gz: PASSED
```

## Parte 2: Subir a GitHub

### 1. Inicializar Git (si aún no lo has hecho)

```bash
# En el directorio del proyecto
git init
git add .
git commit -m "Initial commit: django-flex-importer v1.0.0"
```

### 2. Crear repositorio en GitHub

1. Ve a https://github.com/new
2. Nombre del repositorio: `django-flex-importer`
3. Descripción: "Sistema flexible de importación de datos para Django"
4. Público o Privado (recomendado: Público para open source)
5. **NO** inicialices con README (ya tienes uno)
6. Click "Create repository"

### 3. Conectar y subir

```bash
# Agregar el remote (reemplaza 'tu-usuario')
git remote add origin https://github.com/tu-usuario/django-flex-importer.git

# Renombrar la rama a 'main' (si usas master)
git branch -M main

# Subir el código
git push -u origin main
```

### 4. Configurar GitHub Actions (CI/CD)

Los archivos ya están en `.github/workflows/`:
- `ci.yml`: Ejecuta tests automáticamente en cada push/PR
- `publish.yml`: Publica a PyPI cuando creas un release

**Necesitarás agregar un secreto para PyPI** (ver Parte 3, paso 5).

## Parte 3: Publicar en PyPI

### Opción A: Publicar Manualmente

#### 1. Crear API Token en PyPI

1. Ve a https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Nombre: "django-flex-importer"
4. Scope: "Entire account" (o específico del proyecto después de la primera publicación)
5. Copia el token (empieza con `pypi-...`)
6. **GUÁRDALO**: Solo se muestra una vez

#### 2. Configurar credenciales

```bash
# Crear archivo de configuración
# En Windows: %USERPROFILE%\.pypirc
# En Linux/Mac: ~/.pypirc

nano ~/.pypirc
```

Contenido:
```ini
[pypi]
username = __token__
password = pypi-TU_TOKEN_AQUI
```

#### 3. Limpiar builds anteriores

```bash
rm -rf dist/ build/ *.egg-info
```

#### 4. Construir el paquete

```bash
python -m build
```

Esto crea:
- `dist/django_flex_importer-1.0.0-py3-none-any.whl` (wheel)
- `dist/django-flex-importer-1.0.0.tar.gz` (source)

#### 5. Verificar el paquete

```bash
twine check dist/*
```

#### 6. (Opcional) Probar en TestPyPI primero

```bash
# Subir a TestPyPI
twine upload --repository testpypi dist/*

# Probar instalación
pip install --index-url https://test.pypi.org/simple/ django-flex-importer
```

#### 7. Publicar en PyPI (¡oficial!)

```bash
twine upload dist/*
```

Si todo sale bien, verás:
```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading django_flex_importer-1.0.0-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Uploading django-flex-importer-1.0.0.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

View at:
https://pypi.org/project/django-flex-importer/1.0.0/
```

#### 8. ¡Verificar!

```bash
# Instalar desde PyPI
pip install django-flex-importer

# Probar importación
python -c "from flex_importer import FlexImporter; print('¡Funciona!')"
```

### Opción B: Publicar Automáticamente con GitHub Actions

#### 1. Agregar PyPI Token a GitHub

1. Ve a tu repo: `https://github.com/tu-usuario/django-flex-importer/settings/secrets/actions`
2. Click "New repository secret"
3. Name: `PYPI_API_TOKEN`
4. Value: Tu token de PyPI
5. Click "Add secret"

#### 2. Crear un Release en GitHub

```bash
# 1. Crear un tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# 2. Subir el tag
git push origin v1.0.0
```

#### 3. Crear Release en GitHub UI

1. Ve a `https://github.com/tu-usuario/django-flex-importer/releases/new`
2. Tag: `v1.0.0`
3. Release title: `v1.0.0 - Primera versión pública`
4. Descripción:
   ```markdown
   ## Características

   - Importadores personalizables desde modelos Django
   - Soporte para XLSX, CSV y JSON
   - Validación automática de datos
   - Actualización inteligente con key_field
   - Procesamiento asíncrono con Celery (opcional)
   - Interfaz completa en Django Admin

   ## Instalación

   ```bash
   pip install django-flex-importer
   ```

   ## Documentación

   Ver [README.md](https://github.com/tu-usuario/django-flex-importer#readme)
   ```
5. Click "Publish release"

**GitHub Actions automáticamente:**
- Ejecutará los tests
- Construirá el paquete
- Lo publicará en PyPI

## Parte 4: Después de Publicar

### 1. Actualizar URLs en README

Asegúrate de que todos los badges en README.md apunten a tu repo:

```markdown
[![CI](https://github.com/tu-usuario/django-flex-importer/workflows/CI/badge.svg)]
[![codecov](https://codecov.io/gh/tu-usuario/django-flex-importer/branch/main/graph/badge.svg)]
```

### 2. Agregar badges de PyPI

Los badges se actualizarán automáticamente cuando publiques:
- PyPI version
- Python versions
- Downloads

### 3. Promocionar tu proyecto

- Comparte en Twitter/LinkedIn
- Publica en r/django (Reddit)
- Agrega a Django Packages: https://djangopackages.org/
- Crea un blog post explicando el proyecto

## Publicar Nuevas Versiones

### 1. Actualizar versión

**setup.py** (línea 12):
```python
version='1.1.0',
```

**pyproject.toml** (línea 7):
```toml
version = "1.1.0"
```

### 2. Actualizar CHANGELOG (crear si no existe)

```markdown
# Changelog

## [1.1.0] - 2026-01-15

### Added
- Nueva característica X
- Soporte para Y

### Fixed
- Bug en Z

## [1.0.0] - 2026-01-13

- Versión inicial
```

### 3. Commit y tag

```bash
git add .
git commit -m "Bump version to 1.1.0"
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin main
git push origin v1.1.0
```

### 4. Crear Release en GitHub

O publicar manualmente:

```bash
rm -rf dist/ build/ *.egg-info
python -m build
twine upload dist/*
```

## Troubleshooting

### Error: "The user 'username' isn't allowed to upload to project"

- Asegúrate de usar `__token__` como username, no tu nombre de usuario de PyPI

### Error: "File already exists"

- No puedes subir la misma versión dos veces
- Incrementa la versión en setup.py y pyproject.toml

### Error: "Invalid distribution"

- Ejecuta `twine check dist/*` para ver qué está mal
- Asegúrate de que README.md exista y sea válido

### Los tests de GitHub Actions fallan

- Revisa los logs en `https://github.com/tu-usuario/django-flex-importer/actions`
- Asegúrate de que todas las dependencias estén en setup.py

## Recursos Adicionales

- [Packaging Python Projects](https://packaging.python.org/tutorials/packaging-projects/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## Checklist Final

Antes de publicar, verifica:

- [ ] Actualizada información personal (nombre, email, URLs)
- [ ] Tests pasan localmente: `pytest`
- [ ] Linters pasan: `black`, `flake8`, `isort`
- [ ] `twine check dist/*` pasa
- [ ] README.md está completo y correcto
- [ ] LICENSE tiene tu nombre
- [ ] Versión actualizada en setup.py y pyproject.toml
- [ ] .gitignore está configurado correctamente
- [ ] Repositorio de GitHub creado
- [ ] Token de PyPI creado y guardado
- [ ] (GitHub Actions) Secret PYPI_API_TOKEN agregado

¡Listo para publicar! 🚀
