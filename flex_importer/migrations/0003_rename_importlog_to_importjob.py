# Generated migration

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flex_importer', '0002_auto_20260113_1932'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ImportLog',
            new_name='ImportJob',
        ),
    ]
