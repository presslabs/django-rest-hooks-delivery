Django REST Hooks Delivery
==========================

Various deliverers for `django rest hooks
<https://github.com/zapier/django-rest-hooks>`_ and `django rest hooks ng
<https://github.com/PressLabs/django-rest-hooks-ng>`_.

Installation
------------

To get the latest stable release from PyPi

.. code-block:: bash

    pip install django-rest-hooks-delivery

To get the latest commit from GitHub

.. code-block:: bash

    pip install -e git+git://github.com/PressLabs/django-rest-hooks-delivery.git#egg=rest_hooks_delivery

Add ``rest_hooks_delivery`` to your ``INSTALLED_APPS``

.. code-block:: python

    INSTALLED_APPS = (
        ...,
        'rest_hooks_delivery',
    )

Don't forget to migrate your database

.. code-block:: bash

    ./manage.py migrate rest_hooks_delivery # if you are using django > 1.7

    ./manage.py syncdb rest_hooks_delivery # if you are using django < 1.7


Usage
-----

This application depends on the `django rest hooks
<https://github.com/zapier/django-rest-hooks>`_ application, which is an
unmigrated application. You have to make sure that the `django rest hooks
<https://github.com/zapier/django-rest-hooks>`_ application has been migrated
(sync'd) before you run the migrations for :code:`rest_hooks_delivery`.

Make sure you have added :code:`rest_hooks_delivery` to the list of
:code:`INSTALLED_APPS` before :code:`django.contrib.admin` and that you have
set :code:`HOOK_DELIVERER` to one of the available deliverers. Currently
:code:`rest_hooks_delivery.deliverers.batch` and 
:code:`rest_hooks_delivery.deliverers.retry` are available.

To use the retry deliverer:

This deliverer uses threads to retry failed hook deliveries until they succeed.

.. code-block:: python

    ### settings.py ###

    INSTALLED_APPS = [
    ...
    'rest_hooks_delivery',
    'django.contrib.admin',
    ]

    HOOK_DELIVERER = 'rest_hooks_delivery.deliverers.retry'

It also provides a management command useful for retrying failed hooks.

.. code-block:: bash

    ./manage.py retry_failed_hooks

To use the batch deliverer:

This deliverer tries to minimize server load by using Celery tasks to batch the
hook deliveries. It can batch the deliveries by number of deliveries per target
URL and by time. You can choose one of the batching modes or use both. When
both modes are selected the deliverer will batch by whichever mode occurs
first.

If this deliverer is selected, do not forget to start a celery worker for your
project. Check the `Celery <http://www.celeryproject.org>`_ website for an
example. If this deliverer is set to batch by time, also start the Celery
scheduler for your celery worker. An example of this can be found on the Celery
website too.

Carefully copy the code below.

.. code-block:: python

    ### settings.py

    from datetime import timedelta

    ...

    INSTALLED_APPS = [
    ...
    'rest_hooks_delivery',
    'django.contrib.admin',
    ]

    HOOK_DELIVERER = 'rest_hooks_delivery.deliverers.batch'

    HOOK_DELIVERER_SETTINGS = {
        'batch_by': ['time','size'], # List of batching modes
        # can be ['time'], ['size'] or ['size', 'time']
        'size': 3, # Number of hook events/target url to batch
        'time': 60, # time in seconds
        'retry': True, # Retry failed hook deliveries(True) or discard(False)
    }

    CELERY_TIMEZONE = 'UTC'

    if 'time' in HOOK_DELIVERER_SETTINGS['batch_by']:
        CELERYBEAT_SCHEDULE = {
            'add-time_batch-task': {
                'task': 'rest_hooks_delivery.tasks.time_batch',
                'schedule': timedelta(seconds=HOOK_DELIVERER_SETTINGS['time']),
            }
        }
