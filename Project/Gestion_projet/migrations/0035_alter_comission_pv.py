# Generated by Django 5.0.2 on 2024-04-01 14:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Gestion_projet', '0034_comission_pv_alter_comission_employes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comission',
            name='PV',
            field=models.FileField(blank=True, default=None, null=True, upload_to='pdfs/'),
        ),
    ]
