# Generated by Django 5.0.2 on 2024-05-24 13:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Gestion_projet', '0063_alter_comission_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comission',
            name='type',
            field=models.CharField(choices=[('1', 'CME'), ('2', 'COP'), ('3', 'CEO')], max_length=30),
        ),
    ]
