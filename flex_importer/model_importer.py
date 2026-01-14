"""
Model-based importer for FlexImporter
"""
from django.db import models
from .base import FlexImporter, FlexImporterBase


class FlexModelImporterMeta:
    """Meta options for FlexModelImporter"""
    model = None
    verbose_name = None
    can_re_run = False
    key_field = None
    exclude_fields = []
    include_fields = None


class FlexModelImporterBase(FlexImporterBase):
    """Metaclass for FlexModelImporter to handle model field extraction"""

    def __new__(mcs, name, bases, attrs):
        # Get the Meta class if it exists
        meta = attrs.get('Meta')

        if meta and hasattr(meta, 'model') and meta.model:
            model_class = meta.model

            # Extract fields from the model
            exclude_fields = getattr(meta, 'exclude_fields', [])
            include_fields = getattr(meta, 'include_fields', None)

            # Add common fields to exclude by default
            default_exclude = ['id', 'created_at', 'updated_at']
            exclude_fields = list(set(exclude_fields + default_exclude))

            for field in model_class._meta.get_fields():
                # Skip if not a concrete field
                if not isinstance(field, models.Field):
                    continue

                field_name = field.name

                # Skip excluded fields
                if field_name in exclude_fields:
                    continue

                # If include_fields is specified, only include those fields
                if include_fields is not None and field_name not in include_fields:
                    continue

                # Skip auto fields
                if isinstance(field, (models.AutoField, models.BigAutoField)):
                    continue

                # Clone the field for the importer
                cloned_field = mcs._clone_field(field)
                attrs[field_name] = cloned_field

        return super().__new__(mcs, name, bases, attrs)

    @staticmethod
    def _clone_field(field):
        """Clone a Django model field for use in importer"""
        field_class = field.__class__

        # Get field parameters
        kwargs = {
            'verbose_name': field.verbose_name,
            'blank': field.blank,
            'null': field.null,
        }

        # Add specific parameters based on field type
        if isinstance(field, models.CharField):
            kwargs['max_length'] = field.max_length
        elif isinstance(field, models.DecimalField):
            kwargs['max_digits'] = field.max_digits
            kwargs['decimal_places'] = field.decimal_places
        elif isinstance(field, (models.ForeignKey, models.OneToOneField)):
            # For foreign keys, use IntegerField to accept IDs
            field_class = models.IntegerField
            kwargs['verbose_name'] = f"{field.verbose_name} (ID)"
        elif isinstance(field, models.ManyToManyField):
            # Skip many-to-many fields
            return None

        # Remove null from kwargs if not supported
        if field_class in [models.BooleanField]:
            kwargs.pop('null', None)

        try:
            return field_class(**kwargs)
        except Exception:
            # Fallback to TextField if field creation fails
            return models.TextField(
                verbose_name=kwargs.get('verbose_name', ''),
                blank=kwargs.get('blank', False)
            )


class FlexModelImporter(FlexImporter, metaclass=FlexModelImporterBase):
    """
    Base class for creating model-based importers.

    Instead of defining fields manually, this class automatically extracts
    fields from a Django model.

    Example:
        class SalesModelImporter(FlexModelImporter):
            class Meta:
                model = Sale
                verbose_name = "Importador de Ventas desde Modelo"
                can_re_run = True
                exclude_fields = ['some_field']  # Optional
                include_fields = ['date', 'cliente', 'producto']  # Optional

            def import_action(self, row_data):
                # Create model instance with validated data
                sale = self.Meta.model.objects.create(**row_data)
                return True
    """

    _abstract = True

    class Meta:
        model = None
        verbose_name = None
        can_re_run = False
        key_field = None
        exclude_fields = []
        include_fields = None

    def __init__(self):
        super().__init__()
        if not hasattr(self.Meta, 'model') or not self.Meta.model:
            raise ValueError(
                f"{self.__class__.__name__} must specify a model in Meta class"
            )

    @classmethod
    def get_model(cls):
        """Get the associated model class"""
        if hasattr(cls, 'Meta') and hasattr(cls.Meta, 'model'):
            return cls.Meta.model
        return None

    @classmethod
    def create_instance(cls, validated_data):
        """
        Helper method to create a model instance from validated data.

        Args:
            validated_data (dict): Validated row data

        Returns:
            Model instance or None if creation fails
        """
        model = cls.get_model()
        if not model:
            return None

        try:
            instance = model.objects.create(**validated_data)
            return instance
        except Exception as e:
            raise Exception(f"Error creating {model.__name__}: {str(e)}")

    @classmethod
    def update_or_create_instance(cls, lookup_fields, validated_data):
        """
        Helper method to update or create a model instance.

        Args:
            lookup_fields (dict): Fields to use for lookup (e.g., {'id': 1})
            validated_data (dict): Validated row data

        Returns:
            Tuple of (instance, created)
        """
        model = cls.get_model()
        if not model:
            return None, False

        try:
            instance, created = model.objects.update_or_create(
                **lookup_fields,
                defaults=validated_data
            )
            return instance, created
        except Exception as e:
            raise Exception(f"Error updating/creating {model.__name__}: {str(e)}")

    @classmethod
    def save_instance(cls, validated_data):
        """
        Helper method that automatically handles create/update based on key_field.

        If key_field is defined in Meta, it will try to find an existing instance
        and update it. Otherwise, it will create a new instance.

        Args:
            validated_data (dict): Validated row data

        Returns:
            dict: {'instance': instance, 'action': 'created'/'updated'}
        """
        model = cls.get_model()
        if not model:
            return None

        key_field = cls.get_key_field()

        try:
            if key_field and key_field in validated_data:
                # Try to find existing instance by key_field
                lookup_value = validated_data.get(key_field)
                lookup = {key_field: lookup_value}

                # Separate the lookup field from the data to update
                update_data = {k: v for k, v in validated_data.items() if k != key_field}

                instance, created = model.objects.update_or_create(
                    **lookup,
                    defaults=update_data
                )

                return {
                    'instance': instance,
                    'action': 'created' if created else 'updated'
                }
            else:
                # No key_field, just create
                instance = model.objects.create(**validated_data)
                return {
                    'instance': instance,
                    'action': 'created'
                }

        except Exception as e:
            raise Exception(f"Error saving {model.__name__}: {str(e)}")
