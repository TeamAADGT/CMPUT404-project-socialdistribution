# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-04-08 19:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_post_github_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='author',
            name='has_github_task',
            field=models.BooleanField(default=False),
        ),
    ]