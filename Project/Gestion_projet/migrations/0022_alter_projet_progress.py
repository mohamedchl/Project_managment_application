# Generated by Django 5.0.2 on 2024-03-27 11:50

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Gestion_projet', '0021_alter_projet_progress_alter_tache_progress'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projet',
            name='progress',
            field=models.FloatField(default=0, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)]),
        ),
    ]
