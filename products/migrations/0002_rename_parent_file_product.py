# Generated by Django 4.2 on 2023-05-20 08:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='file',
            old_name='parent',
            new_name='product',
        ),
    ]