# Generated by Django 2.2.7 on 2022-01-20 02:32

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('swmadmin', '0014_auto_20220113_1441'),
        ('reports', '0015_unlogged_tracklog_history'),
    ]

    operations = [
        migrations.CreateModel(
            name='Unlogged_tracklog_history_v2',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField(auto_now=True, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, default=0, max_digits=9)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, default=0, max_digits=9)),
                ('speed', models.FloatField(blank=True, default=0.0)),
                ('heading', models.IntegerField(blank=True, null=True)),
                ('mps', models.BooleanField(default=0, null=True)),
                ('miv', models.FloatField(blank=True, default=0.0)),
                ('ibv', models.FloatField(blank=True, default=0.0)),
                ('location', django.contrib.gis.db.models.fields.PointField(blank=True, null=True, spatial_index=False, srid=4326)),
                ('ignition', models.BooleanField(default=1)),
                ('emergency', models.CharField(blank=True, max_length=4, null=True)),
                ('dio', models.CharField(blank=True, max_length=150, null=True)),
                ('dod', models.DateField(auto_now=True, null=True)),
                ('shift', models.CharField(choices=[('1', 'Morning'), ('2', 'Afternoon'), ('3', 'Night')], default='1', max_length=1)),
                ('created_at', models.DateTimeField(auto_now=True, null=True)),
                ('vehicle', models.ForeignKey(db_index=False, on_delete=django.db.models.deletion.CASCADE, related_name='unlogged_tracklog_historys_v2s', to='swmadmin.Vehicle')),
            ],
            options={
                'db_table': 'unlogged_tracklog_historys_v2',
                'ordering': ['vehicle', 'datetime'],
            },
        ),
    ]
