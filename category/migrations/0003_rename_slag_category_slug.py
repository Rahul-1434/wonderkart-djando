# Generated by Django 5.2.3 on 2025-06-22 03:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('category', '0002_alter_category_slag'),
    ]

    operations = [
        migrations.RenameField(
            model_name='category',
            old_name='slag',
            new_name='slug',
        ),
    ]
