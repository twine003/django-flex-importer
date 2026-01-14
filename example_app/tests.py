"""
Tests for FlexImporter and FlexModelImporter
"""
from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from .models import Sale
from .importers import SalesImporter, SalesModelImporter


class FlexImporterTestCase(TestCase):
    """Test FlexImporter base class"""

    def test_sales_importer_fields(self):
        """Test that SalesImporter has correct fields"""
        fields = SalesImporter.get_fields()

        self.assertIn('date', fields)
        self.assertIn('cliente', fields)
        self.assertIn('producto', fields)
        self.assertIn('cantidad', fields)
        self.assertIn('precio', fields)

    def test_sales_importer_validation(self):
        """Test field validation"""
        test_date = timezone.now()
        row_data = {
            'date': test_date,
            'cliente': 'Juan Pérez',
            'producto': '101',
            'cantidad': '5',
            'precio': '29.99'
        }

        validated_data, errors = SalesImporter.validate_row(row_data)

        self.assertEqual(len(errors), 0, f"Validation errors: {errors}")
        self.assertEqual(validated_data['cliente'], 'Juan Pérez')
        self.assertEqual(validated_data['producto'], 101)
        self.assertEqual(validated_data['cantidad'], 5)
        self.assertEqual(validated_data['precio'], Decimal('29.99'))

    def test_sales_importer_import_action(self):
        """Test import action creates Sale"""
        importer = SalesImporter()

        row_data = {
            'date': timezone.now(),
            'cliente': 'Test Cliente',
            'producto': 100,
            'cantidad': 2,
            'precio': Decimal('19.99')
        }

        result = importer.import_action(row_data)

        self.assertTrue(result)
        self.assertEqual(Sale.objects.count(), 1)

        sale = Sale.objects.first()
        self.assertEqual(sale.cliente, 'Test Cliente')
        self.assertEqual(sale.producto, 100)
        self.assertEqual(sale.cantidad, 2)


class FlexModelImporterTestCase(TestCase):
    """Test FlexModelImporter class"""

    def test_model_importer_extracts_fields(self):
        """Test that FlexModelImporter extracts fields from model"""
        fields = SalesModelImporter.get_fields()

        # Should have extracted fields from Sale model
        self.assertIn('date', fields)
        self.assertIn('cliente', fields)
        self.assertIn('producto', fields)
        self.assertIn('cantidad', fields)
        self.assertIn('precio', fields)

        # Should exclude auto fields
        self.assertNotIn('id', fields)
        self.assertNotIn('created_at', fields)

    def test_model_importer_get_model(self):
        """Test that get_model returns correct model"""
        model = SalesModelImporter.get_model()
        self.assertEqual(model, Sale)

    def test_model_importer_create_instance(self):
        """Test create_instance helper method"""
        row_data = {
            'date': timezone.now(),
            'cliente': 'Model Test',
            'producto': 200,
            'cantidad': 3,
            'precio': Decimal('39.99')
        }

        sale = SalesModelImporter.create_instance(row_data)

        self.assertIsNotNone(sale)
        self.assertEqual(sale.cliente, 'Model Test')
        self.assertEqual(sale.producto, 200)
        self.assertEqual(Sale.objects.count(), 1)

    def test_model_importer_import_action(self):
        """Test import action using FlexModelImporter"""
        importer = SalesModelImporter()

        row_data = {
            'date': timezone.now(),
            'cliente': 'Model Import Test',
            'producto': 300,
            'cantidad': 5,
            'precio': Decimal('49.99')
        }

        result = importer.import_action(row_data)

        self.assertTrue(result)
        self.assertEqual(Sale.objects.count(), 1)

        sale = Sale.objects.first()
        self.assertEqual(sale.cliente, 'Model Import Test')
        self.assertEqual(sale.producto, 300)

    def test_model_importer_update_or_create(self):
        """Test update_or_create_instance helper method"""
        # Create initial sale
        initial_data = {
            'date': timezone.now(),
            'cliente': 'Original Cliente',
            'producto': 400,
            'cantidad': 1,
            'precio': Decimal('10.00')
        }

        sale1, created1 = SalesModelImporter.update_or_create_instance(
            {'producto': 400},
            initial_data
        )

        self.assertTrue(created1)
        self.assertEqual(Sale.objects.count(), 1)
        self.assertEqual(sale1.cliente, 'Original Cliente')

        # Update existing sale
        updated_data = {
            'date': timezone.now(),
            'cliente': 'Updated Cliente',
            'producto': 400,
            'cantidad': 10,
            'precio': Decimal('15.00')
        }

        sale2, created2 = SalesModelImporter.update_or_create_instance(
            {'producto': 400},
            updated_data
        )

        self.assertFalse(created2)
        self.assertEqual(Sale.objects.count(), 1)
        self.assertEqual(sale2.id, sale1.id)
        self.assertEqual(sale2.cliente, 'Updated Cliente')
        self.assertEqual(sale2.cantidad, 10)

    def test_model_importer_validation_same_as_regular(self):
        """Test that validation works the same for both importers"""
        test_date = timezone.now()
        row_data = {
            'date': test_date,
            'cliente': 'Test',
            'producto': '500',
            'cantidad': '7',
            'precio': '99.99'
        }

        validated1, errors1 = SalesImporter.validate_row(row_data)
        validated2, errors2 = SalesModelImporter.validate_row(row_data)

        self.assertEqual(len(errors1), len(errors2))
        self.assertEqual(validated1['producto'], validated2['producto'])
        self.assertEqual(validated1['cantidad'], validated2['cantidad'])
