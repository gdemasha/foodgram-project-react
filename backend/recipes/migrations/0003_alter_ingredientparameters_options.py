# Generated by Django 3.2.3 on 2024-03-02 11:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ingredientparameters',
            options={'default_related_name': 'ingredient_parameters', 'verbose_name': 'ингредиент с количеством', 'verbose_name_plural': 'Ингредиенты с количеством'},
        ),
    ]
