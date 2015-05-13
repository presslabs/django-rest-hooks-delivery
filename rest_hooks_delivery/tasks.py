# -*- coding: utf-8 -*-
# vim: ft=python:sw=4:ts=4:sts=4:et:
from __future__ import absolute_import

from celery import shared_task

from rest_hooks_delivery.models import StoredHook

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
