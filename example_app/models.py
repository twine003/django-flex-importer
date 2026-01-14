"""
Example models
"""
from django.db import models


class Sale(models.Model):
    """Model to store sales data"""

    date = models.DateTimeField(verbose_name='Fecha')
    cliente = models.TextField(verbose_name='Cliente')
    producto = models.IntegerField(verbose_name='Producto ID')
    cantidad = models.IntegerField(verbose_name='Cantidad', default=1)
    precio = models.DecimalField(verbose_name='Precio', max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-date']

    def __str__(self):
        return f"{self.cliente} - {self.date.strftime('%Y-%m-%d')}"

class Product(models.Model):
    """Model to store product data"""
    sku = models.CharField(verbose_name='SKU', max_length=50, unique=True)
    nombre = models.CharField(verbose_name='Nombre del Producto', max_length=200)
    precio = models.DecimalField(verbose_name='Precio', max_digits=10, decimal_places=2)
    stock = models.IntegerField(verbose_name='Stock Inicial')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre