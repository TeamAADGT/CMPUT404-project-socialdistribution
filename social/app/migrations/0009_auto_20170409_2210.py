# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-04-09 22:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_merge_20170409_1832'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='count',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='post',
            name='nxt',
            field=models.URLField(default=b'url'),
        ),
        migrations.AddField(
            model_name='post',
            name='size',
            field=models.IntegerField(default=1),
        ),
    ]
