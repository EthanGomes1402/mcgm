# Generated by Django 2.2.7 on 2020-09-09 20:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('swmadmin', '0004_stop_station_ward'),
    ]

    operations = [
        migrations.AlterField(
            model_name='route',
            name='code',
            field=models.CharField(max_length=20, null=True, unique=True),
        ),
    ]
