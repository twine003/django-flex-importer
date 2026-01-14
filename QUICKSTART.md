# Guía Rápida - FlexModelImporter

Esta guía te muestra cómo crear un importador en **menos de 10 líneas de código**.

## Paso 1: Define tu Modelo (ya lo tienes)

```python
# models.py
from django.db import models

class Sale(models.Model):
    date = models.DateTimeField(verbose_name='Fecha')
    cliente = models.TextField(verbose_name='Cliente')
    producto = models.IntegerField(verbose_name='Producto ID')
    cantidad = models.IntegerField(verbose_name='Cantidad', default=1)
    precio = models.DecimalField(verbose_name='Precio', max_digits=10, decimal_places=2)
```

## Paso 2: Crea el Importador (¡Solo 12 líneas!)

```python
# importers.py
from flex_importer.model_importer import FlexModelImporter
from .models import Sale


class SalesModelImporter(FlexModelImporter):
    class Meta:
        model = Sale
        verbose_name = "Importador de Ventas"
        can_re_run = True

    def import_action(self, row_data):
        self.create_instance(row_data)
        return True
```

## Paso 3: Usa el Importador

1. Ve al admin: http://localhost:8000/admin/
2. Click en "Bitácoras de Importación" → "Nueva Importación"
3. Selecciona "Importador de Ventas"
4. Descarga la plantilla (XLSX, CSV o JSON)
5. Llena la plantilla con tus datos
6. Sube el archivo
7. ¡Listo!

## Comparación: FlexImporter vs FlexModelImporter

### Con FlexImporter (Manual - 30+ líneas)
```python
class SalesImporter(FlexImporter):
    # Tienes que definir TODOS los campos manualmente
    date = models.DateTimeField(verbose_name='Fecha de Venta')
    cliente = models.TextField(verbose_name='Nombre del Cliente')
    producto = models.IntegerField(verbose_name='ID del Producto')
    cantidad = models.IntegerField(verbose_name='Cantidad', blank=True)
    precio = models.DecimalField(verbose_name='Precio', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Importador de Ventas"
        can_re_run = True

    def import_action(self, row_data):
        if row_data.get('cantidad') is None:
            row_data['cantidad'] = 1

        sale = Sale.objects.create(
            date=row_data['date'],
            cliente=row_data['cliente'],
            producto=row_data['producto'],
            cantidad=row_data['cantidad'],
            precio=row_data['precio']
        )
        return True
```

### Con FlexModelImporter (Automático - 12 líneas)
```python
class SalesModelImporter(FlexModelImporter):
    # ¡Los campos se extraen automáticamente del modelo!
    class Meta:
        model = Sale
        verbose_name = "Importador de Ventas"
        can_re_run = True

    def import_action(self, row_data):
        self.create_instance(row_data)
        return True
```

## Características Avanzadas

### Excluir campos específicos
```python
class Meta:
    model = Sale
    exclude_fields = ['created_at', 'updated_at']
```

### Incluir solo campos específicos
```python
class Meta:
    model = Sale
    include_fields = ['date', 'cliente', 'producto']
```

### Actualizar o Crear (Upsert)
```python
def import_action(self, row_data):
    lookup = {'producto': row_data.pop('producto')}
    sale, created = self.update_or_create_instance(lookup, row_data)
    return True
```

### Lógica personalizada
```python
def import_action(self, row_data):
    # Validación personalizada
    if row_data['precio'] < 0:
        return "El precio no puede ser negativo"

    # Valores por defecto
    row_data.setdefault('cantidad', 1)

    # Crear instancia
    self.create_instance(row_data)
    return True
```

## ¿Cuándo usar cada uno?

### Usa FlexModelImporter cuando:
- ✅ Quieres sincronización automática con el modelo
- ✅ Los campos del modelo son suficientes
- ✅ Prefieres menos código y más mantenibilidad

### Usa FlexImporter cuando:
- ✅ Necesitas campos diferentes a los del modelo
- ✅ Quieres validaciones muy específicas
- ✅ Los campos de importación no coinciden con el modelo

## ¡Eso es todo!

Con FlexModelImporter, crear un importador toma **menos de 2 minutos**. 🚀
