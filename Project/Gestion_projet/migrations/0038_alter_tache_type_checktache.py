# Generated by Django 5.0.2 on 2024-04-02 15:33

import datetime
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Gestion_projet', '0037_tache_tache_mere_tache_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tache',
            name='type',
            field=models.CharField(choices=[('1', 'Tâche simple'), ('2', 'Tâche besoin d un suivi ')], default='1', max_length=10),
        ),
        migrations.CreateModel(
            name='CheckTache',
            fields=[
                ('id_check', models.AutoField(primary_key=True, serialize=False)),
                ('date', models.DateField(default=datetime.datetime.now)),
                ('tache_finis', models.BooleanField(default=False)),
                ('tache', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checkTache', to='Gestion_projet.tache')),
            ],
        ),
    ]
