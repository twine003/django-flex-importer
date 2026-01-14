# Datos de Ejemplo

Esta carpeta contiene archivos de ejemplo para probar el sistema de importación.

## Archivos Disponibles

### ventas_ejemplo.csv
Archivo CSV con 5 ventas de ejemplo. Úsalo para probar el "Importador de Ventas (desde Modelo)".

### ventas_ejemplo.json
El mismo contenido en formato JSON.

## Cómo Usar

1. Ve al admin: http://localhost:8000/admin/
2. Click en "Bitácoras de Importación" → "Nueva Importación"
3. Selecciona "Importador de Ventas (desde Modelo)"
4. Selecciona el formato (CSV o JSON)
5. Sube el archivo correspondiente
6. Click en "Importar"

## Resultado Esperado

- Total de filas: 5
- Filas exitosas: 5
- Filas con error: 0
- Estado: Exitoso

Las 5 ventas se crearán en la base de datos y podrás verlas en la sección "Ventas" del admin.

## Prueba con Errores

Para probar la validación de errores, puedes modificar los archivos:

- Elimina un campo requerido (ej: cliente)
- Pon un texto en un campo numérico (ej: "abc" en producto)
- Usa un formato de fecha incorrecto

El sistema detectará los errores y los mostrará en la bitácora.
