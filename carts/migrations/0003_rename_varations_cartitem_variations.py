# Generated by Django 5.2.3 on 2025-06-25 16:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('carts', '0002_cartitem_varations'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cartitem',
            old_name='varations',
            new_name='variations',
        ),
    ]
