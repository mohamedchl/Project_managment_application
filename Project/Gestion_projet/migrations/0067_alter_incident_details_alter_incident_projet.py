# Generated by Django 5.0.2 on 2024-06-02 00:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Gestion_projet', '0066_alter_comission_titre'),
    ]

    operations = [
        migrations.AlterField(
            model_name='incident',
            name='details',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='incident',
            name='projet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Gestion_projet.projet'),
        ),
    ]
