# Generated migration for ImporterPermission proxy model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flex_importer', '0003_rename_importlog_to_importjob'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImporterPermission',
            fields=[
            ],
            options={
                'managed': False,
                'default_permissions': (),
                'permissions': [],
            },
        ),
    ]
