#!/usr/bin/env python

import sys
import django

from django.conf import settings
from django.apps import apps


APP_NAME = 'rest_hooks_delivery'

settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
        }
    },
    USE_TZ=True,
    CELERY_ALWAYS_EAGER=True,
    ROOT_URLCONF='{0}.tests'.format(APP_NAME),
    MIDDLEWARE_CLASSES=(
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
    ),
    SITE_ID=1,
    HOOK_EVENTS={},
    HOOK_DELIVERER='rest_hooks_delivery.deliverers.batch',
    BROKER_URL='redis://localhost:6379/1',
    HOOK_DELIVERER_SETTINGS={
        'size': 5,
        'time': 5,
        'retry': {
            'retries': 1,
            'retry_interval': 5,
        },
    },
    HOOK_THREADING=False,
    INSTALLED_APPS=(
        APP_NAME,
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.admin',
        'django.contrib.sites',
        'django_comments',
        'rest_hooks',
    ),
)

if hasattr(django, 'setup'):
    django.setup()

from django.test.utils import get_runner
TestRunner = get_runner(settings)
test_runner = TestRunner()
failures = test_runner.run_tests([APP_NAME])
if failures:
    sys.exit(failures)
