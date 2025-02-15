# Generated by Django 5.0.2 on 2024-04-01 17:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Gestion_projet', '0036_alter_document_tache'),
    ]

    operations = [
        migrations.AddField(
            model_name='tache',
            name='tache_mere',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sous_taches', to='Gestion_projet.tache'),
        ),
        migrations.AddField(
            model_name='tache',
            name='type',
            field=models.CharField(choices=[('1', 'Tâche simple'), ('2', 'Tâche complexe')], default='1', max_length=10),
        ),
    ]
