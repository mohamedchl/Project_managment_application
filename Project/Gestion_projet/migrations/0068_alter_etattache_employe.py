# Generated by Django 5.0.2 on 2024-06-02 00:10

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Gestion_projet', '0067_alter_incident_details_alter_incident_projet'),
    ]

    operations = [
        migrations.AlterField(
            model_name='etattache',
            name='employe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checktaches', to='Gestion_projet.employe'),
        ),
    ]
