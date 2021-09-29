# Generated by Django 2.2.7 on 2020-09-01 15:46

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('swmadmin', '0002_auto_20200901_2059'),
    ]

    operations = [
        migrations.CreateModel(
            name='Weight_history',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weight', models.FloatField(blank=True, default=0.0)),
                ('datetime', models.DateTimeField(auto_now=True, null=True)),
                ('shift', models.CharField(choices=[('1', 'Morning'), ('2', 'Afternoon'), ('3', 'Night')], default='1', max_length=1)),
                ('stop_station', models.ForeignKey(limit_choices_to={'is_dmpgnd': True}, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='weight_historys', to='swmadmin.Stop_station')),
                ('vehicle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='weight_historys', to='swmadmin.Vehicle')),
            ],
            options={
                'db_table': 'weight_historys',
                'ordering': ['datetime'],
            },
        ),
        migrations.CreateModel(
            name='Tracklog_history',
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
                ('location', django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326)),
                ('ignition_status', models.BooleanField(default=1)),
                ('emergency_status', models.CharField(blank=True, max_length=4, null=True)),
                ('digital_io_status', models.CharField(blank=True, max_length=25, null=True)),
                ('created_at', models.DateTimeField(auto_now=True, null=True)),
                ('vehicle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tracklog_historys', to='swmadmin.Vehicle')),
            ],
            options={
                'db_table': 'tracklog_historys',
                'ordering': ['created_at', 'datetime'],
            },
        ),
        migrations.CreateModel(
            name='Tag_read_history',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, default=0, max_digits=9)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, default=0, max_digits=9)),
                ('tag', models.CharField(max_length=30, null=True)),
                ('read_at', models.DateTimeField(auto_now=True, null=True)),
                ('is_registered', models.BooleanField(default=0)),
                ('tag_type', models.CharField(choices=[('B', 'Bin'), ('W', 'Windschield')], default='B', max_length=1)),
                ('vehicle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tag_read_historys', to='swmadmin.Vehicle')),
            ],
            options={
                'db_table': 'tag_read_historys',
            },
        ),
        migrations.CreateModel(
            name='Route_status',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shift', models.CharField(choices=[('1', 'Morning'), ('2', 'Afternoon'), ('3', 'Night')], default='1', max_length=1)),
                ('status', models.BooleanField(default=0)),
                ('date', models.DateField()),
                ('bins', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='route_statuses', to='swmadmin.Bin')),
                ('route', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='route_statuses', to='swmadmin.Route')),
            ],
            options={
                'db_table': 'route_statuses',
            },
        ),
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('1', 'Geo Fence'), ('2', 'Power Disconnection'), ('3', 'Route Deviation'), ('4', 'Speed Violation')], default='1', max_length=1)),
                ('sub_category', models.CharField(choices=[('0', 'None'), ('1', 'central workshop'), ('2', 'department offices'), ('3', 'department workshop'), ('4', 'dumping ground'), ('5', 'garbage collection point'), ('6', 'maintainance sites'), ('7', 'motor loading chowkies'), ('8', 'station location'), ('9', 'swd workshops'), ('10', 'swm garages'), ('11', 'swm offices'), ('12', 'transfer stations'), ('13', 'ward offices'), ('14', 'work site')], default='0', max_length=2)),
                ('message', models.TextField()),
                ('location', django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326)),
                ('created_at', models.DateTimeField(auto_now=True, null=True)),
                ('vehicle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alerts', to='swmadmin.Vehicle')),
            ],
            options={
                'db_table': 'alerts',
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='Activity_log_history',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.DateTimeField(auto_now=True, null=True)),
                ('speed', models.FloatField(blank=True, default=0.0)),
                ('halt_type', models.CharField(choices=[('S', 'Stop_station'), ('B', 'Bin')], default='S', max_length=1)),
                ('day_of_duty', models.DateField()),
                ('vehicle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activity_log_historys', to='swmadmin.Vehicle')),
            ],
            options={
                'db_table': 'activity_log_historys',
            },
        ),
    ]
