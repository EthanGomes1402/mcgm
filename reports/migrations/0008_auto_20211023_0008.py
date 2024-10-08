# Generated by Django 2.2.7 on 2021-10-23 00:08
from psqlextra.backend.migrations.operations import PostgresAddRangePartition

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0007_auto_20211023_0007'),
    ]

    operations = [
        PostgresAddRangePartition(
            model_name="Vehicle_tracklog_history",
            name="1_2_2002",
            from_values='2002-01-01 05:55:01',
            to_values='2002-03-01 05:55:00',
        ),
        PostgresAddRangePartition(
            model_name="Vehicle_tracklog_history",
            name="3_4_2002",
            from_values='2002-03-01 05:55:01',
            to_values='2002-05-01 05:55:00',
        ),
        PostgresAddRangePartition(
            model_name="Vehicle_tracklog_history",
            name="5_6_2002",
            from_values='2002-05-01 05:55:01',
            to_values='2002-07-01 05:55:00',
        ),
        PostgresAddRangePartition(
            model_name="Vehicle_tracklog_history",
            name="7_8_2002",
            from_values='2002-07-01 05:55:01',
            to_values='2002-09-01 05:55:00',
        ),
        PostgresAddRangePartition(
            model_name="Vehicle_tracklog_history",
            name="9_10_2002",
            from_values='2002-09-01 05:55:01',
            to_values='2002-11-01 05:55:00',
        ),
        PostgresAddRangePartition(
            model_name="Vehicle_tracklog_history",
            name="11_12_2002",
            from_values='2002-11-01 05:55:01',
            to_values='2003-01-01 05:55:00',
        ),
    ]
