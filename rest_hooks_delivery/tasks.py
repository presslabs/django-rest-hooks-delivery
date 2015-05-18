# -*- coding: utf-8 -*-
# vim: ft=python:sw=4:ts=4:sts=4:et:
from __future__ import absolute_import

from celery import shared_task

from rest_hooks_delivery.models import StoredHook

from django.conf import settings

import requests, json

BATCH_DELIVERER = 'rest_hooks_delivery.deliverers.batch_hooks'
HOOK_DELIVERER = getattr(settings, 'HOOK_DELIVERER', None)
HOOK_DELIVERER_SETTINGS = getattr(settings, 'HOOK_DELIVERER_SETTINGS', None)

if HOOK_DELIVERER == BATCH_DELIVERER  and\
    HOOK_DELIVERER_SETTINGS is None:
    raise Exception("You need to define settings.HOOK_DELIVERER_SETTINGS!")

@shared_task
def store_hook(*args, **kwargs):
    target_url = kwargs.pop('url')
    hook_event = kwargs.pop('_hook_event')
    hook_user_id = kwargs.pop('_hook_user_id')
    hook_payload = kwargs.get('data', '{}')
    hook = kwargs.pop('_hook_id')

    StoredHook.objects.create(
        target=target_url,
        event=hook_event,
        user_id=hook_user_id,
        payload=hook_payload,
        hook_id=hook
    )

    if HOOK_DELIVERER_SETTINGS['batch_by'] is 'size':
        # check size for current target
        current_count = StoredHook.objects.filter(target=target_url).count()

        # (>=) because if retry is True then count can be > size
        if current_count >= HOOK_DELIVERER_SETTINGS['size']:
            batch_and_send(target_url)

def batch_and_send(target_url):
    events = StoredHook.objects.filter(target=target_url)
    batch_data_list = []
    for event in events:
        batch_data_list.append(event.payload)
    r = requests.post(
        target_url,
        data=json.dumps(batch_data_list),
        headers={'Content-Type': 'application/json'})
    if (r.status_code > 299 and not HOOK_DELIVERER_SETTINGS['retry']) or\
        (r.status_code < 300):
        events.delete()
