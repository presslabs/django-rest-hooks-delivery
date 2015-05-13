# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('rest_hooks', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('rest_hooks_delivery', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StoredHook',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('target', models.URLField(verbose_name='Original target URL', db_index=True, max_length=255, editable=False)),
                ('event', models.CharField(verbose_name='Event', choices=[('campaign.published', 'campaign.published'), ('campaign.unpublished', 'campaign.unpublished')], db_index=True, max_length=64, editable=False)),
                ('payload', models.TextField(editable=False)),
                ('hook', models.ForeignKey(to='rest_hooks.Hook', editable=False)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, editable=False)),
            ],
        ),
    ]
