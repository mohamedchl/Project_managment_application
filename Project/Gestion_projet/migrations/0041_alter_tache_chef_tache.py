# Generated by Django 5.0.2 on 2024-04-04 03:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Gestion_projet', '0040_tache_chef_tache'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tache',
            name='chef_tache',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='chef_taches', to='Gestion_projet.employe'),
        ),
    ]
