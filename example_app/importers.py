"""
Example importers using FlexImporter and FlexModelImporter
"""
from django.db import models
from flex_importer.base import FlexImporter
from flex_importer.model_importer import FlexModelImporter
from .models import Sale, Product


class SalesImporter(FlexImporter):
    """
    Importer for sales data.

    This will appear in the admin with the verbose_name "Importador de Ventas"
    and can be re-run after completion.
    """

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
        can_re_run = True

    def import_action(self, row_data):
        """
        Custom import logic.

        This method receives validated data and should create the Sale object.
        Return True on success, or an error message on failure.
        """
        try:
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

        except Exception as e:
            return f"Error al crear venta: {str(e)}"


class SalesModelImporter(FlexModelImporter):
    """
    Model-based importer for sales data.

    This automatically extracts fields from the Sale model,
    so you don't need to define them manually.

    Uses 'producto' as key_field, so re-running will update existing
    sales with the same product ID instead of creating duplicates.
    """

    class Meta:
        model = Sale
        verbose_name = "Importador de Ventas (desde Modelo)"
        can_re_run = True
        key_field = 'producto'  # Use producto as key for update/create
        # Optional: exclude specific fields
        # exclude_fields = ['some_field']
        # Optional: include only specific fields
        # include_fields = ['date', 'cliente', 'producto', 'cantidad', 'precio']

    def import_action(self, row_data):
        """
        Simple import using the model with automatic update/create.

        The save_instance helper automatically checks if a record with
        the same 'producto' exists and updates it, or creates a new one.
        """
        try:
            # Set default value for optional fields
            if row_data.get('cantidad') is None:
                row_data['cantidad'] = 1

            # Use save_instance which respects key_field
            result = self.save_instance(row_data)

            # Return info about what happened
            return result  # Returns {'instance': instance, 'action': 'created'/'updated'}

        except Exception as e:
            return f"Error al guardar venta: {str(e)}"


class ProductImporter(FlexImporter):
    """
    Example of another importer that cannot be re-run.
    """

    sku = models.CharField(verbose_name='SKU', max_length=50)
    nombre = models.CharField(verbose_name='Nombre del Producto', max_length=200)
    precio = models.DecimalField(verbose_name='Precio', max_digits=10, decimal_places=2)
    stock = models.IntegerField(verbose_name='Stock Inicial')

    class Meta:
        verbose_name = "Importador de Productos"
        can_re_run = True

    def import_action(self, row_data):
        """
        This is just an example. In a real application, you would create
        Product objects here.
        """
        print(f"Importando producto: {row_data}")
        return True

class ProductModelImporter(FlexModelImporter):
    """
    Model-based importer for product data.

    Uses 'sku' as key_field, so re-running will update existing
    products with the same SKU instead of creating duplicates.
    """

    class Meta:
        model = Product
        key_field = 'sku'
        verbose_name = "Importador de Productos (desde Modelo)"
        can_re_run = True

    def import_action(self, row_data):
        """
        Simple import using the model with automatic update/create.

        The save_instance helper automatically checks if a record with
        the same 'sku' exists and updates it, or creates a new one.
        """
        try:
            # Use save_instance which respects key_field
            result = self.save_instance(row_data)

            # Return info about what happened
            return result  # Returns {'instance': instance, 'action': 'created'/'updated'}

        except Exception as e:
            return f"Error al guardar producto: {str(e)}"