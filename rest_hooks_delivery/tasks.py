# -*- coding: utf-8 -*-
# vim: ft=python:sw=4:ts=4:sts=4:et:
from __future__ import absolute_import

from celery import shared_task

from rest_hooks_delivery.models import StoredHook

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

import requests, json, redis

BATCH_DELIVERER = 'rest_hooks_delivery.deliverers.batch'
HOOK_DELIVERER = getattr(settings, 'HOOK_DELIVERER', None)
HOOK_DELIVERER_SETTINGS = getattr(settings, 'HOOK_DELIVERER_SETTINGS', None)

BATCH_LOCK = 'batch_lock'

if HOOK_DELIVERER == BATCH_DELIVERER  and\
    HOOK_DELIVERER_SETTINGS is None:
    raise Exception("You need to define settings.HOOK_DELIVERER_SETTINGS!")

@shared_task
def store_hook(*args, **kwargs):
    target_url = kwargs.get('url')
    current_count = store_and_count(*args, **kwargs)

    print(HOOK_DELIVERER_SETTINGS)

    # If first in queue and batching by time
    if 'time' in HOOK_DELIVERER_SETTINGS:
        if current_count == 1:
            batch_and_send.apply_async(args=(target_url,),
                countdown=HOOK_DELIVERER_SETTINGS['time'],
                link_error=fail_handler.s(target_url))
    
    if 'size' in HOOK_DELIVERER_SETTINGS:
        # (>=) because if retry is True count can be > size
        if current_count >= HOOK_DELIVERER_SETTINGS['size']:
            batch_and_send.apply_async(args=(target_url,),
                countdown=0,
                link_error=fail_handler.s(target_url))

def store_and_count(*args, **kwargs):
    count = None
    target_url = kwargs.pop('url')
    hook_event = kwargs.pop('_hook_event')
    hook_user_id = kwargs.pop('_hook_user_id')
    hook_payload = kwargs.get('data', '{}')
    hook = kwargs.pop('_hook_id')

    with redis.Redis().lock(BATCH_LOCK):
        StoredHook.objects.create(
            target=target_url,
            event=hook_event,
            user_id=hook_user_id,
            payload=hook_payload,
            hook_id=hook
        )

        count = StoredHook.objects.filter(target=target_url).count()

    return count

@shared_task
def fail_handler(uuid, target_url):
    clear_events(target_url)

def clear_events(target_url):
    with redis.Redis().lock(BATCH_LOCK):
        events = StoredHook.objects.filter(target=target_url).delete()

@shared_task
def batch_and_send(target_url):
    events = None
    with redis.Redis().lock(BATCH_LOCK):
        try:
            events = StoredHook.objects.filter(target=target_url)
            batch_data_list = []
            for event in events:
                batch_data_list.append(event.payload)

            if len(batch_data_list):
                r = requests.post(
                    target_url,
                    data=json.dumps(batch_data_list, cls=DjangoJSONEncoder),
                    headers={'Content-Type': 'application/json'})
                if (r.status_code > 299 and not 'retry' in HOOK_DELIVERER_SETTINGS)\
                    or (r.status_code < 300):
                    #print('in -', HOOK_DELIVERER_SETTINGS)
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
