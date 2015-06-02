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

class TimeBatchTest(TestCase):
    """
    This test Class uses real HTTP calls to a requestbin service, making it easy
    to check responses and endpoint history.
    """

    #############
    ### TOOLS ###
    #############

    def setUp(self):
        #self.HOOK_EVENTS = getattr(settings, 'HOOKS_EVENTS', None)
        #self.HOOK_DELIVERER = getattr(settings, 'HOOK_DELIVERER', None)
        #self.HOOK_DELIVERER_SETTINGS = \
        #    getattr(settings, 'HOOK_DELIVERER_SETTINGS', None)
        self.client = requests # force non-async for test cases

        self.user = User.objects.create_user('bob', 'bob@example.com', 'password')
        self.site = Site.objects.create(domain='example.com', name='example.com')

        rh_models.HOOK_EVENTS = {
            'comment.added':      'django_comments.Comment.created',
        }

        #settings.HOOK_DELIVERER = 'rest_hooks_delivery.deliverers.batch'

        app = Celery('rest_hooks_delivery_tests')
        app.config_from_object('django.conf:settings')

    #def tearDown(self):
        #settings.HOOK_DELIVERER = self.HOOK_DELIVERER
        #settings.HOOK_DELIVERER_SETTINGS = self.HOOK_DELIVERER_SETTINGS

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
    @override_settings(HOOK_DELIVERER_SETTINGS={'time': 7})
    def test_batching_by_time(self, method_mock):
        # this test assumes all test_comments can be created within test_time
        test_time = 7
        test_comments = 2

        #print(settings.HOOK_DELIVERER_SETTINGS)

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

        #payload = json.loads(method_mock.call_args_list[0][1]['data'])
        print(len(method_mock.call_args_list))

        # payload contains all comments
        #self.assertEquals(len(payload), len(comments))

        # hooks cleared after delivery
        #self.assertEquals(StoredHook.objects.all().count(), 0)

