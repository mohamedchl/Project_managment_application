# Generated by Django 5.0.2 on 2024-04-01 15:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Gestion_projet', '0035_alter_comission_pv'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='tache',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='Gestion_projet.tache'),
        ),
    ]
