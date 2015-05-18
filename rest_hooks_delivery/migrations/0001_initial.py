# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FailedHook',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('last_retry', models.DateTimeField(auto_now=True, db_index=True)),
                ('target', models.URLField(verbose_name=b'Original target URL', max_length=255, editable=False, db_index=True)),
                ('event', models.CharField(db_index=True, verbose_name=b'Event', max_length=64, editable=False, choices=[(b'customer.created', b'customer.created'), (b'customer.deleted', b'customer.deleted'), (b'customer.updated', b'customer.updated'), (b'invoice.created', b'invoice.created'), (b'invoice.deleted', b'invoice.deleted'), (b'invoice.updated', b'invoice.updated'), (b'plan.created', b'plan.created'), (b'plan.deleted', b'plan.deleted'), (b'plan.updated', b'plan.updated'), (b'proforma.created', b'proforma.created'), (b'proforma.deleted', b'proforma.deleted'), (b'proforma.updated', b'proforma.updated'), (b'provider.created', b'provider.created'), (b'provider.deleted', b'provider.deleted'), (b'provider.updated', b'provider.updated'), (b'subscription.created', b'subscription.created'), (b'subscription.deleted', b'subscription.deleted'), (b'subscription.updated', b'subscription.updated')])),
                ('payload', models.TextField(editable=False)),
                ('response_headers', models.TextField(max_length=65535, editable=False)),
                ('response_body', models.TextField(max_length=65535, editable=False)),
                ('last_status', models.PositiveSmallIntegerField(editable=False, db_index=True)),
                ('retries', models.PositiveIntegerField(default=1, editable=False, db_index=True)),
                ('hook', models.ForeignKey(editable=False, to='rest_hooks.Hook')),
                ('user', models.ForeignKey(editable=False, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-last_retry',),
            },
        ),
        migrations.AlterUniqueTogether(
            name='failedhook',
            unique_together=set([('target', 'event', 'user', 'hook')]),
        ),
    ]
