# Guía de key_field - Actualización Automática de Registros

El parámetro `key_field` permite que tus importadores actualicen registros existentes en lugar de crear duplicados cuando se re-procesa una importación.

## ¿Qué es key_field?

`key_field` es un campo de tu modelo que se usa como identificador único para buscar registros existentes. Si se encuentra un registro con el mismo valor en ese campo, se actualiza; si no, se crea uno nuevo.

## Ejemplo Básico

```python
class SalesModelImporter(FlexModelImporter):
    class Meta:
        model = Sale
        verbose_name = "Importador de Ventas"
        can_re_run = True
        key_field = 'producto'  # Usa 'producto' como clave única

    def import_action(self, row_data):
        result = self.save_instance(row_data)
        return result
```

## Cómo Funciona

### Sin key_field (Comportamiento por Defecto)

```python
# Primera importación
producto: 101, cliente: "Juan", cantidad: 5
# Resultado: Crea registro ID=1

# Segunda importación (mismo producto)
producto: 101, cliente: "María", cantidad: 10
# Resultado: Crea registro ID=2 (duplicado)
```

### Con key_field='producto'

```python
# Primera importación
producto: 101, cliente: "Juan", cantidad: 5
# Resultado: Crea registro ID=1

# Segunda importación (mismo producto)
producto: 101, cliente: "María", cantidad: 10
# Resultado: Actualiza registro ID=1 con nuevos datos
```

## Método save_instance()

El método `save_instance()` es un helper de `FlexModelImporter` que automáticamente maneja la lógica de crear/actualizar basándose en `key_field`.

### Retorno

```python
{
    'instance': <objeto_del_modelo>,
    'action': 'created'  # o 'updated'
}
```

### Uso en import_action

```python
def import_action(self, row_data):
    try:
        result = self.save_instance(row_data)

        # El procesador detecta automáticamente si fue creado o actualizado
        return result

    except Exception as e:
        return f"Error: {str(e)}"
```

## Estadísticas en la Bitácora

Cuando usas `key_field` con `save_instance()`, la bitácora mostrará:

- **Filas Procesadas**: Total de filas procesadas
- **Filas Exitosas**: Total de operaciones exitosas
- **Filas Creadas**: Cuántas se crearon
- **Filas Actualizadas**: Cuántas se actualizaron
- **Filas con Error**: Cuántas fallaron

### Ejemplo de Mensaje de Resultado

```
Importación completada exitosamente. 10 filas procesadas (3 creadas, 7 actualizadas).
```

## Casos de Uso

### 1. Catálogo de Productos

```python
class ProductModelImporter(FlexModelImporter):
    class Meta:
        model = Product
        key_field = 'sku'  # SKU es único por producto
        can_re_run = True

    def import_action(self, row_data):
        result = self.save_instance(row_data)
        return result
```

**Beneficio**: Puedes re-importar el catálogo completo y solo actualiza los precios/stock sin duplicar productos.

### 2. Usuarios/Clientes

```python
class CustomerImporter(FlexModelImporter):
    class Meta:
        model = Customer
        key_field = 'email'  # Email único por cliente
        can_re_run = True

    def import_action(self, row_data):
        result = self.save_instance(row_data)
        return result
```

**Beneficio**: Actualiza información de clientes existentes sin crear duplicados.

### 3. Transacciones/Ventas

```python
class TransactionImporter(FlexModelImporter):
    class Meta:
        model = Transaction
        key_field = 'transaction_id'  # ID único de transacción
        can_re_run = True

    def import_action(self, row_data):
        result = self.save_instance(row_data)
        return result
```

**Beneficio**: Puedes corregir datos de transacciones pasadas sin crear duplicados.

## Comparación de Métodos

### create_instance() - Siempre Crea

```python
def import_action(self, row_data):
    # Siempre crea un nuevo registro
    instance = self.create_instance(row_data)
    return True
```

**Estadística**: Solo incrementa "Filas Creadas"

### save_instance() - Crea o Actualiza

```python
def import_action(self, row_data):
    # Crea si no existe, actualiza si existe (según key_field)
    result = self.save_instance(row_data)
    return result
```

**Estadísticas**: Incrementa "Filas Creadas" o "Filas Actualizadas" según corresponda

### update_or_create_instance() - Control Manual

```python
def import_action(self, row_data):
    # Control manual del campo de búsqueda
    lookup = {'producto': row_data.pop('producto')}
    instance, created = self.update_or_create_instance(lookup, row_data)

    return {
        'instance': instance,
        'action': 'created' if created else 'updated'
    }
```

**Uso**: Cuando necesitas lógica personalizada o búsqueda por múltiples campos

## Ventajas de usar key_field

✅ **Previene Duplicados**: No crea registros duplicados al re-importar
✅ **Actualizaciones Fáciles**: Puedes corregir datos simplemente re-importando
✅ **Estadísticas Claras**: Sabes exactamente cuántos registros se crearon vs actualizaron
✅ **Re-procesamiento Seguro**: Puedes ejecutar la misma importación múltiples veces sin problemas
✅ **Sincronización de Datos**: Ideal para mantener bases de datos sincronizadas

## Ejemplo Completo

```python
# models.py
class Product(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()

# importers.py
class ProductModelImporter(FlexModelImporter):
    class Meta:
        model = Product
        verbose_name = "Importador de Productos"
        can_re_run = True
        key_field = 'sku'  # SKU es único

    def import_action(self, row_data):
        try:
            # Validaciones personalizadas
            if row_data.get('price', 0) < 0:
                return "El precio no puede ser negativo"

            # Guardar (crear o actualizar automáticamente)
            result = self.save_instance(row_data)

            return result

        except Exception as e:
            return f"Error: {str(e)}"
```

### Archivo de Importación (productos.csv)

```csv
SKU,Nombre del Producto,Precio,Stock
PROD001,Laptop Dell,999.99,10
PROD002,Mouse Logitech,29.99,50
PROD003,Teclado Mecánico,79.99,25
```

### Primera Importación

```
Resultado: 3 filas procesadas (3 creadas, 0 actualizadas)
- PROD001: Creado
- PROD002: Creado
- PROD003: Creado
```

### Segunda Importación (con precios actualizados)

```csv
SKU,Nombre del Producto,Precio,Stock
PROD001,Laptop Dell,899.99,15
PROD002,Mouse Logitech,24.99,60
PROD004,Webcam HD,49.99,30
```

```
Resultado: 3 filas procesadas (1 creada, 2 actualizadas)
- PROD001: Actualizado (precio: 999.99 → 899.99, stock: 10 → 15)
- PROD002: Actualizado (precio: 29.99 → 24.99, stock: 50 → 60)
- PROD004: Creado
```

## Consejos

1. **Elige un campo único**: El `key_field` debería ser un campo que identifique únicamente cada registro (ej: SKU, email, transaction_id)

2. **Define unique=True en el modelo**: Para prevenir duplicados a nivel de base de datos:
   ```python
   sku = models.CharField(max_length=50, unique=True)
   ```

3. **Usa can_re_run=True**: Si defines `key_field`, generalmente querrás permitir re-ejecuciones:
   ```python
   class Meta:
       key_field = 'sku'
       can_re_run = True
   ```

4. **Retorna el resultado de save_instance()**: Para que las estadísticas funcionen correctamente:
   ```python
   return self.save_instance(row_data)  # ✅ Correcto
   # NO: self.save_instance(row_data); return True  # ❌ Estadísticas incorrectas
   ```

## Limitaciones

- Solo soporta un campo como clave (no múltiples campos)
- El campo debe existir en `row_data` para que funcione la actualización
- Si el campo no es único en la base de datos, puede actualizar el registro incorrecto

Para casos más complejos, usa `update_or_create_instance()` con lógica personalizada.
