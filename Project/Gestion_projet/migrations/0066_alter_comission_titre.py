# Generated by Django 5.0.2 on 2024-06-01 22:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Gestion_projet', '0065_alter_etatprojet_date_etat_alter_projet_date_debut_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comission',
            name='titre',
            field=models.CharField(max_length=60),
        ),
    ]
