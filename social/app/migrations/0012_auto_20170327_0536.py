# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-03-27 11:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0011_merge_20170327_0515'),
    ]

    operations = [
        migrations.AlterField(
            model_name='node',
            name='host',
            field=models.CharField(max_length=512, unique=True),
        ),
    ]