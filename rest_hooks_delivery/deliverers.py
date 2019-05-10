# -*- coding: utf-8 -*-
# vim: ft=python:sw=4:ts=4:sts=4:et:
import collections
import json
import threading

import requests

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import F
from rest_hooks.utils import get_module

from rest_hooks_delivery.models import FailedHook


class FlushThread(threading.Thread):
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.client = client

    def run(self):
        self.client.sync_flush()


class Client(object):
    """
    Manages a simple pool of threads to flush the queue of requests.
    """
    def __init__(self, num_threads=3):
        self.queue = collections.deque()

        self.flush_lock = threading.Lock()
        self.num_threads = num_threads
        self.flush_threads = [FlushThread(self) for _ in
                              range(self.num_threads)]
        self.total_sent = 0

    def enqueue(self, method, *args, **kwargs):
        self.queue.append((method, args, kwargs))
        self.refresh_threads()

    def get(self, *args, **kwargs):
        self.enqueue('get', *args, **kwargs)

    def post(self, *args, **kwargs):
        self.enqueue('post', *args, **kwargs)

    def put(self, *args, **kwargs):
        self.enqueue('put', *args, **kwargs)

    def delete(self, *args, **kwargs):
        self.enqueue('delete', *args, **kwargs)

    def refresh_threads(self):
        with self.flush_lock:
            # refresh if there are jobs to do and no threads are alive
            if len(self.queue) > 0:
                to_refresh = [index for index, thread in
                              enumerate(self.flush_threads)
                              if not thread.is_alive()]
                for index in to_refresh:
                    self.flush_threads[index] = FlushThread(self)
                    self.flush_threads[index].start()

    def sync_flush(self):
        while len(self.queue) > 0:
            method, args, kwargs = self.queue.pop()
            hook_id = kwargs.pop('_hook_id')
            hook_event = kwargs.pop('_hook_event')
            hook_user_id = kwargs.pop('_hook_user_id')
            failed_hook = kwargs.pop('_failed_hook')

            try:
                r = None
                r = getattr(requests, method)(*args, **kwargs)
                payload = kwargs.get('data', '{}')
                if r.status_code > 299:
                    
                    if failed_hook:
                        if failed_hook.retries == 5:
                            # send email after several failed attempts, 
                            # so that the issue can be investigated
                            r.raise_for_status()

                        failed_hook.response_headers = {k: r.headers[k] for k in
                                                        r.headers.iterkeys()}
                        failed_hook.response_body = r.content
                        failed_hook.last_status = r.status_code
                        failed_hook.retries = F('retries') + 1
                        failed_hook.save()

                    else:
                        FailedHook.objects.create(
                            target=r.request.url,
                            payload=payload,
                            response_headers={k: r.headers[k]
                                              for k in r.headers.iterkeys()},
                            response_body=r.content,
                            last_status=r.status_code,
                            event=hook_event,
                            user_id=hook_user_id,
                            hook_id=hook_id
                        )

                elif failed_hook:
                    failed_hook.delete()

                self.total_sent += 1

            except (requests.exceptions.HTTPError, requests.exceptions.Timeout, 
                requests.exceptions.RequestException, requests.exceptions.SSLError) as e:

                send_mail = False

                # record failed hook for retrying
                if failed_hook:
                    send_mail = failed_hook.retries == 5
                    failed_hook.response_headers = {k: r.headers[k] for k in
                                                    r.headers.iterkeys()}
                    failed_hook.response_body = r.content
                    failed_hook.last_status = r.status_code
                    failed_hook.retries = F('retries') + 1
                    failed_hook.save()

                else:
                    send_mail = True    #TODO: Consider not sending it on the first go
                    FailedHook.objects.create(
                        target=r.request.url,
                        payload=payload,
                        response_headers={k: r.headers[k]
                                          for k in r.headers.iterkeys()},
                        response_body=r.content,    # TODO: Test what happens when there is no response, e.g. with SSLError
                        last_status=r.status_code,
                        event=hook_event,
                        user_id=hook_user_id,
                        hook_id=hook_id
                    )

                if send_mail and getattr(settings, 'HOOK_EXCEPTION_MAILER', None):
                    if 'data' in kwargs:
                        kwargs['data'] = json.loads(kwargs['data'])
                    extra_body = { 'webhook': kwargs }

                    if r is not None:
                        extra_body['response'] = {
                            'status_code': r.status_code,
                            'url': r.url,
                            'reason': r.reason,
                            'content': r.content,
                        }

                    mailer = get_module(settings.HOOK_EXCEPTION_MAILER)
                    mailer('Error sending webhook', request=None, exception=e, extra_body=extra_body)


client = Client()


def retry(target, payload, instance=None, hook=None, failed_hook=None, **kwargs):
    event = hook.event
    if isinstance(payload, basestring):
        payload_dict = json.loads(payload)
        if 'hook' in payload_dict and 'event' in payload_dict['hook']:
            event = payload_dict['hook']['event']

    client.post(
        url=target,
        data=json.dumps(payload, cls=DjangoJSONEncoder) if not isinstance(payload, basestring) else payload,
        headers={'Content-Type': 'application/json'},
        _hook_id=hook.pk,
        _hook_event=event,
        _hook_user_id=hook.user.pk,
        _failed_hook=failed_hook
    )
