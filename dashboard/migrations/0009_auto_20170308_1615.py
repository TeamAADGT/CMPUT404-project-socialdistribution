# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-03-08 23:15
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0008_auto_20170308_1256'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='UserProfile',
            new_name='Author',
        ),
    ]
