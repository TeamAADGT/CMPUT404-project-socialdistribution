# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-04-09 22:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_merge_20170409_1832'),
    ]

    operations = [
        migrations.AddField(
            model_name='author',
            name='email',
            field=models.EmailField(blank=True, default=b'', max_length=254),
        ),
        migrations.AddField(
            model_name='author',
            name='first_name',
            field=models.TextField(blank=True, default=b''),
        ),
        migrations.AddField(
            model_name='author',
            name='last_name',
            field=models.TextField(blank=True, default=b''),
        ),
    ]
