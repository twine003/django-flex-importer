"""
Admin for example app
"""
from django.contrib import admin
from .models import Sale, Product


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['id', 'date', 'cliente', 'producto', 'cantidad', 'precio', 'created_at']
    list_filter = ['date', 'created_at']
    search_fields = ['cliente']
    ordering = ['-date']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'sku', 'nombre', 'precio', 'stock', 'created_at']
    search_fields = ['sku', 'nombre']
    ordering = ['nombre']