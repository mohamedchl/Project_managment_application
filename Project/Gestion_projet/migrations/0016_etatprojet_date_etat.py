# Generated by Django 5.0.2 on 2024-03-25 15:19

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Gestion_projet', '0015_alter_notification_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='etatprojet',
            name='date_etat',
            field=models.DateField(default=datetime.datetime.now),
        ),
    ]
