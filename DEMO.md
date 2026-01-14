# Demo de FlexModelImporter

Este documento muestra un ejemplo real de cómo usar el sistema.

## 1. Inicia el servidor

```bash
python manage.py runserver
```

## 2. Accede al Admin

Ve a: http://localhost:8000/admin/

Usuario: (el superusuario que creaste)

## 3. Ve a "Bitácoras de Importación"

Verás la lista de importaciones anteriores (vacía al inicio).

## 4. Haz clic en "Nueva Importación"

Aparecerá un formulario con:
- **Importador**: Selector con todos los importadores registrados
- **Formato**: XLSX, CSV o JSON
- **Archivo**: Para subir tu archivo

## 5. Selecciona un Importador

Verás 3 opciones:
1. **Importador de Ventas** (FlexImporter manual)
2. **Importador de Ventas (desde Modelo)** (FlexModelImporter automático)
3. **Importador de Productos** (FlexImporter sin re-run)

Selecciona "Importador de Ventas (desde Modelo)"

## 6. Descarga la Plantilla

Aparecerán 3 botones:
- Descargar XLSX
- Descargar CSV
- Descargar JSON

Descarga el formato que prefieras.

### Ejemplo de Plantilla XLSX:

| Fecha de Venta * | Nombre del Cliente * | ID del Producto * | Cantidad | Precio Unitario * |
|------------------|---------------------|-------------------|----------|-------------------|
|                  |                     |                   |          |                   |

Los campos con `*` son requeridos.

## 7. Llena la Plantilla

### Ejemplo XLSX:
| Fecha de Venta      | Nombre del Cliente | ID del Producto | Cantidad | Precio Unitario |
|---------------------|-------------------|-----------------|----------|-----------------|
| 2024-01-15 10:30:00 | Juan Pérez        | 101             | 5        | 29.99           |
| 2024-01-15 14:20:00 | María García      | 102             | 2        | 45.50           |
| 2024-01-16 09:15:00 | Carlos López      | 103             | 1        | 120.00          |

### Ejemplo CSV:
```csv
Fecha de Venta,Nombre del Cliente,ID del Producto,Cantidad,Precio Unitario
2024-01-15 10:30:00,Juan Pérez,101,5,29.99
2024-01-15 14:20:00,María García,102,2,45.50
2024-01-16 09:15:00,Carlos López,103,1,120.00
```

### Ejemplo JSON:
```json
{
  "data": [
    {
      "date": "2024-01-15T10:30:00",
      "cliente": "Juan Pérez",
      "producto": 101,
      "cantidad": 5,
      "precio": "29.99"
    },
    {
      "date": "2024-01-15T14:20:00",
      "cliente": "María García",
      "producto": 102,
      "cantidad": 2,
      "precio": "45.50"
    },
    {
      "date": "2024-01-16T09:15:00",
      "cliente": "Carlos López",
      "producto": 103,
      "cantidad": 1,
      "precio": "120.00"
    }
  ]
}
```

## 8. Sube el Archivo

1. Selecciona el formato (debe coincidir con tu archivo)
2. Sube el archivo
3. Haz clic en "Importar"

## 9. Ver el Resultado

Serás redirigido al detalle de la importación donde verás:

### Estado
- Badge con el estado (Exitoso, Parcial, Fallido)

### Estadísticas
- Total de filas: 3
- Filas procesadas: 3
- Filas exitosas: 3
- Filas con error: 0
- Tasa de éxito: 100%

### Log de Progreso
Verás algo como:
```
[2024-01-17T10:00:00] Iniciando importación...
[2024-01-17T10:00:00] Se encontraron 3 filas para procesar
[2024-01-17T10:00:01] Importación completada exitosamente. 3 filas procesadas.
```

### Detalles de Errores
(Si hay errores, verás el número de fila y el mensaje de error)

### Archivo Original
Link para descargar el archivo que subiste

## 10. Ver los Datos Importados

Ve a "Ventas" en el admin y verás las 3 ventas importadas.

## 11. Re-ejecutar Importación

Si el importador tiene `can_re_run = True`:

1. En el detalle de la importación, verás el botón "Re-ejecutar"
2. Haz clic y se creará una nueva importación con el mismo archivo
3. Útil para corregir errores en el código de importación

## Errores Comunes

### Error: "El campo 'Cliente' es requerido"
- Solución: Asegúrate de llenar todos los campos marcados con *

### Error: "No se pudo convertir el valor '29.99' al tipo integer"
- Solución: Verifica que el tipo de dato sea correcto (texto vs número)

### Error: "No se pudo convertir el valor 'abc' al tipo datetime"
- Solución: Usa formato ISO para fechas: `YYYY-MM-DDTHH:MM:SS`

## Ventajas del Sistema

1. **Sin código duplicado**: Define el modelo una vez, úsalo para importar
2. **Validación automática**: No necesitas escribir código de validación
3. **Múltiples formatos**: Soporta XLSX, CSV, JSON sin cambios
4. **Bitácora completa**: Sabes exactamente qué pasó en cada importación
5. **Re-ejecución**: Puedes volver a correr importaciones anteriores
6. **Extensible**: Agrega lógica personalizada en `import_action()`

## Comparación con Importación Manual

### Forma tradicional (sin FlexImporter):
```python
# Necesitas escribir:
# 1. Parser de archivos (XLSX, CSV, JSON)
# 2. Validación de cada campo
# 3. Manejo de errores
# 4. Logging
# 5. UI de importación
# = ~500 líneas de código
```

### Con FlexModelImporter:
```python
class SalesModelImporter(FlexModelImporter):
    class Meta:
        model = Sale
        verbose_name = "Importador de Ventas"
        can_re_run = True

    def import_action(self, row_data):
        self.create_instance(row_data)
        return True

# = 8 líneas de código
# Todo lo demás es automático
```

## Siguientes Pasos

1. Crea tu propio modelo
2. Define un importador con `FlexModelImporter`
3. Descarga plantillas y comienza a importar

¡Es así de simple! 🎉
