# Generated by Django 5.0.2 on 2024-03-09 11:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Gestion_projet', '0005_alter_employe_matricule'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employe',
            name='telephone',
            field=models.BigIntegerField(blank=True, null=True),
        ),
    ]
