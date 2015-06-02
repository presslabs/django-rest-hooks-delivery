import requests
import time
from mock import patch, MagicMock, ANY
from django.http import HttpResponse, HttpResponseBadRequest

from datetime import datetime

try:
    # Django <= 1.6 backwards compatibility
    from django.utils import simplejson as json
except ImportError:
    # Django >= 1.7
    import json

from django.conf import settings
from django.contrib.auth.models import User
from django_comments.models import Comment
from django.contrib.sites.models import Site
from django.test import TestCase, override_settings

from rest_hooks_delivery import models as rhd_models
StoredHook = rhd_models.StoredHook

from rest_hooks import models as rh_models
Hook = rh_models.Hook

from celery import Celery

class SizeBatchTest(TestCase):
    """
    This test Class uses real HTTP calls to a requestbin service, making it easy
    to check responses and endpoint history.
    """

    #############
    ### TOOLS ###
    #############

    def setUp(self):
        self.client = requests # force non-async for test cases

        self.user = User.objects.create_user('bob', 'bob@example.com', 'password')
        self.site = Site.objects.create(domain='example.com', name='example.com')

        rh_models.HOOK_EVENTS = {
            'comment.added':      'django_comments.Comment.created',
        }

        app = Celery('rest_hooks_delivery_tests')
        app.config_from_object('django.conf:settings')


    def make_hook(self, event, target):
        return Hook.objects.create(
            user=self.user,
            event=event,
            target=target
        )

    ############
    ### TEST ###
    ############

    @patch('requests.post', autospec=True)
    @override_settings(HOOK_DELIVERER_SETTINGS={'size': 5})
    def test_batching_by_size(self, method_mock):
        test_size = 5
        
        method_mock.return_value = HttpResponse()

        target = 'http://example.com/test_batching_by_size'
        hook = self.make_hook('comment.added', target)

        comment_strings = ['test comment' for x in range(0,test_size - 1)]
        
        comments = [Comment.objects.create(
            site=self.site,
            content_object=self.user,
            user=self.user,
            comment=comment) for comment in comment_strings
        ]

        # hooks are stored while < 'size'
        self.assertEquals(StoredHook.objects.all().count(), len(comments))

        comments.append(Comment.objects.create(
            site=self.site,
            content_object=self.user,
            user=self.user,
            comment='last comment'
            )
        )

        payload = json.loads(method_mock.call_args_list[0][1]['data'])

        # correct payload is delivered to target
        self.assertEquals(len(payload), test_size)

        # hooks cleared after delivery
        self.assertEquals(StoredHook.objects.all().count(), 0)

    @patch('requests.post', autospec=True)
    @override_settings(HOOK_DELIVERER_SETTINGS={'time': 7})
    def test_batching_by_time(self, method_mock):
        # this test assumes all test_comments can be created within test_time
        # it won't matter because of CELERY_ALWAYS_EAGER setting
        # This causes celery to not wait
        # Indication of a passing test will be all the events sent immediately
        test_time = 7
        test_comments = 2

        method_mock.return_value = HttpResponse()

        target = 'http://example.com/test_batching_by_time'
        hook = self.make_hook('comment.added', target)

        comment_strings = ['test comment' for x in range(0, test_comments)]

        comments = [Comment.objects.create(
            site=self.site,
            content_object=self.user,
            user=self.user,
            comment=comment) for comment in comment_strings
        ]

        payloads = [json.loads(args[1]['data']) for args in \
            method_mock.call_args_list]

        # payload contains all comments
        self.assertEquals(len(payloads), len(comments))

        # hooks cleared after delivery
        self.assertEquals(StoredHook.objects.all().count(), 0)

    @patch('requests.post', autospec=True)
    @override_settings(HOOK_DELIVERER_SETTINGS={
    	'size': 5,
    	'retry': {
            'retries': 2,
            'retry_interval': 5
    	}
    })
    def test_retrying_failed_deliveries(self, method_mock):
        test_size = 5

        method_mock.return_value = HttpResponseBadRequest()

        target = 'http://example.com/test_retrying_failed_deliveries'
        hook = self.make_hook('comment.added', target)

        comment_strings = ['test comment' for x in range(0, test_size)]

        comments = [Comment.objects.create(
            site=self.site,
            content_object=self.user,
            user=self.user,
            comment=comment) for comment in comment_strings
        ]

        payloads = [json.loads(args_list[1]['data']) for args_list in \
            method_mock.call_args_list]

        # 3 payloads because of 2 retries
        self.assertEquals(len(payloads), 3)

        # each payload has all comments
        # note that in practise this can be > size
        # if more comments were added since a fail
        for payload in payloads:
            self.assertEquals(len(payload), 5)
