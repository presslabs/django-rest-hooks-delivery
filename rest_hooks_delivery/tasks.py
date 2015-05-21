# -*- coding: utf-8 -*-
# vim: ft=python:sw=4:ts=4:sts=4:et:
from __future__ import absolute_import

from celery import shared_task

from rest_hooks_delivery.models import StoredHook

from django.conf import settings

import requests, json

BATCH_DELIVERER = 'rest_hooks_delivery.deliverers.batch'
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

    current_count = None

    # If first in queue and batching by time
    if 'time' in HOOK_DELIVERER_SETTINGS:
        current_count = event_count_for(target_url)
        if current_count == 1:
            batch_and_send.apply_async(args=(target_url,),
                countdown=HOOK_DELIVERER_SETTINGS['time'],
                link_error=fail_handler.s(target_url))
    
    if 'size' in HOOK_DELIVERER_SETTINGS:
        # check size for current target
        if current_count is None:
            current_count = event_count_for(target_url)

        # (>=) because if retry is True then count can be > size
        if current_count >= HOOK_DELIVERER_SETTINGS['size']:
            batch_and_send.apply_async(args=(target_url,),
                countdown=0,
                link_error=fail_handler.s(target_url))


def event_count_for(target_url):
    events = StoredHook.objects.filter(target=target_url)
    return events.count()

@shared_task
def fail_handler(uuid, target_url):
    events = StoredHook.objects.filter(target=target_url)
    events.delete()

@shared_task
def batch_and_send(target_url):
    events = None
    try:
        events = StoredHook.objects.filter(target=target_url)
        batch_data_list = []
        for event in events:
            batch_data_list.append(event.payload)
        r = requests.post(
            target_url,
            data=json.dumps(batch_data_list),
            headers={'Content-Type': 'application/json'})
        if (r.status_code > 299 and not 'retry' in HOOK_DELIVERER_SETTINGS) or\
            (r.status_code < 300):
            events.delete()
        elif (r.status_code > 299 and 'retry' in HOOK_DELIVERER_SETTINGS):
            if batch_and_send.request.retries == \
                HOOK_DELIVERER_SETTINGS['retry']['retries']:
                events.delete()
            else:
                raise batch_and_send.retry(
                    args=(target_url,),
                    countdown=\
                        HOOK_DELIVERER_SETTINGS['retry']['retry_interval'])
    except requests.exceptions.ConnectionError as exc:
        if 'retry' in HOOK_DELIVERER_SETTINGS:
            if batch_and_send.request.retries == \
                HOOK_DELIVERER_SETTINGS['retry']['retries']:
                events.delete()
            else:
                raise batch_and_send.retry(
                    args=(target_url,), exc=exc,
                    countdown=\
                        HOOK_DELIVERER_SETTINGS['retry']['retry_interval'])
        else:
            events.delete()
