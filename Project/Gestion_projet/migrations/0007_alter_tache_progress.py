# Generated by Django 5.0.2 on 2024-03-09 21:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Gestion_projet', '0006_alter_employe_telephone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tache',
            name='progress',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
