# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2018-02-13 20:21
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0024_auto_20171115_1653'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='exportrun',
            options={'managed': True, 'verbose_name': 'ExportRun (DataPack)', 'verbose_name_plural': 'ExportRuns (DataPacks)'},
        ),
    ]
