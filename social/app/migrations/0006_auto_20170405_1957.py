# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-04-06 01:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_post_child_post'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='child_post',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='parent_post', to='app.Post'),
        ),
    ]
