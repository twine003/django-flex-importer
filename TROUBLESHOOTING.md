# Solución de Problemas

## Problema: El importador crea duplicados en lugar de actualizar

### Síntoma
Cuando re-ejecutas una importación con `key_field` definido, se crean registros duplicados en lugar de actualizar los existentes.

### Causa
El método `import_action()` está usando `create_instance()` en lugar de `save_instance()`.

### Diferencia entre métodos

| Método | Comportamiento | Usa key_field | Retorno |
|--------|---------------|---------------|---------|
| `create_instance()` | Siempre crea nuevo | ❌ No | `instance` |
| `save_instance()` | Crea o actualiza | ✅ Sí | `{'instance': obj, 'action': 'created'/'updated'}` |
| `update_or_create_instance()` | Control manual | ✅ Sí | `(instance, created)` |

### Solución

**❌ Incorrecto** (siempre crea):
```python
class ProductModelImporter(FlexModelImporter):
    class Meta:
        model = Product
        key_field = 'sku'

    def import_action(self, row_data):
        product = self.create_instance(row_data)  # ❌ Ignora key_field
        return True
```

**✅ Correcto** (crea o actualiza):
```python
class ProductModelImporter(FlexModelImporter):
    class Meta:
        model = Product
        key_field = 'sku'

    def import_action(self, row_data):
        result = self.save_instance(row_data)  # ✅ Usa key_field
        return result
```

### Prevenir duplicados a nivel de base de datos

Agrega `unique=True` al campo clave en tu modelo:

```python
class Product(models.Model):
    sku = models.CharField(max_length=50, unique=True)  # ✅ Previene duplicados
```

Luego crea y aplica la migración:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Limpiar duplicados existentes

Si ya tienes duplicados, puedes usar este script:

```python
# clean_duplicates.py
from example_app.models import Product
from collections import defaultdict

products_by_sku = defaultdict(list)

for product in Product.objects.all().order_by('sku', '-created_at'):
    products_by_sku[product.sku].append(product)

for sku, products in products_by_sku.items():
    if len(products) > 1:
        keep = products[0]  # Mantener el más reciente
        for product in products[1:]:
            product.delete()  # Eliminar duplicados

print("Duplicados eliminados")
```

---

## Problema: No veo el botón "Re-ejecutar"

### Síntoma
El botón de re-ejecutar no aparece en la página de detalle de la importación.

### Causas posibles

1. **La importación no ha terminado**
   - El botón solo aparece cuando el estado es: `success`, `partial` o `failed`
   - No aparece en: `pending` o `processing`

2. **can_re_run es False en la base de datos**
   - Aunque tu clase tenga `can_re_run = True`, el valor en la BD puede ser diferente
   - Esto ocurre si cambiaste el valor después de crear la importación

3. **El importador no tiene can_re_run = True**
   - Verifica que tu clase tenga `can_re_run = True` en Meta

### Solución

Sincroniza los metadatos de las importaciones existentes:

```bash
# Ver qué se actualizaría
python manage.py sync_import_metadata --dry-run

# Aplicar cambios
python manage.py sync_import_metadata
```

Este comando actualiza:
- ✅ `can_re_run` según la clase del importador
- ✅ `importer_name` según la clase del importador

---

## Problema: Los colores se ven mal en modo oscuro

### Síntoma
Los formularios o botones se ven con colores incorrectos cuando el admin está en modo oscuro.

### Solución
Los templates ya incluyen soporte para modo oscuro usando variables CSS de Django. Si encuentras algún elemento sin soporte, usa:

```css
/* Light mode */
.mi-elemento {
    background-color: var(--body-bg, white);
    color: var(--body-fg, #333);
}

/* Dark mode - Método 1: Atributo data-theme */
[data-theme="dark"] .mi-elemento {
    background-color: var(--body-bg, #1e1e1e);
    color: var(--body-fg, #e0e0e0);
}

/* Dark mode - Método 2: Media query */
@media (prefers-color-scheme: dark) {
    body:not([data-theme="light"]) .mi-elemento {
        background-color: var(--body-bg, #1e1e1e);
        color: var(--body-fg, #e0e0e0);
    }
}
```

---

## Problema: Las estadísticas no muestran creados/actualizados

### Síntoma
La bitácora solo muestra "filas exitosas" pero no dice cuántas fueron creadas vs actualizadas.

### Causa
El método `import_action()` está retornando `True` en lugar del resultado de `save_instance()`.

### Solución

**❌ Incorrecto**:
```python
def import_action(self, row_data):
    result = self.save_instance(row_data)
    return True  # ❌ Pierde la información de created/updated
```

**✅ Correcto**:
```python
def import_action(self, row_data):
    result = self.save_instance(row_data)
    return result  # ✅ Retorna {'action': 'created'/'updated'}
```

---

## Más Ayuda

- 📖 [README.md](README.md) - Documentación completa
- 🚀 [QUICKSTART.md](QUICKSTART.md) - Guía rápida
- 🔑 [KEY_FIELD_GUIDE.md](KEY_FIELD_GUIDE.md) - Guía de key_field
- 🎬 [DEMO.md](DEMO.md) - Demo paso a paso
