# Generated by Django 2.2.7 on 2020-09-08 12:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
        ('swmadmin', '0003_auto_20200901_2119'),
    ]

    operations = [
        migrations.AddField(
            model_name='stop_station',
            name='ward',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='stop_stations', to='common.Ward'),
        ),
    ]
