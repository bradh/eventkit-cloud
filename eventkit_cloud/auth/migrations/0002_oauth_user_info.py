# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2018-03-06 20:48
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eventkit_cloud.auth', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='oauth',
            name='user_info',
            field=django.contrib.postgres.fields.jsonb.JSONField(default={}),
        ),
    ]
