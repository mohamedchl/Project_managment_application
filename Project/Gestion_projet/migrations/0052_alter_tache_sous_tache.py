# Generated by Django 5.0.2 on 2024-04-18 17:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Gestion_projet', '0051_alter_tache_sous_tache'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tache',
            name='sous_tache',
            field=models.ManyToManyField(blank=True, to='Gestion_projet.tache'),
        ),
    ]
