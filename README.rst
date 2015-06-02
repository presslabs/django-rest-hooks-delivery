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
:code:`rest_hooks_delivery.deliverers.retry` and 
:code:`rest_hooks_delivery.deliverers.batch` are available.

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

This deliverer tries to minimize server load by using Celery + Redis tasks to
batch the hook deliveries. This deliverer operates on a per target URL basis.
Everything explained in the rest of this section assumes this.
The deliverer has 2 modes.

size
`````
.. code-block:: python

  HOOK_DELIVERER_SETTINGS = {
      ...
      'size': 3, # Number of hook events per target URL
      ...
  }

In size mode the deliverer will check the :code:`size` setting and batch the
hooks whenever they reach the specified size.

time
`````
.. code-block:: python
  
  HOOK_DELIVERER_SETTINGS = {
      ...
      'time': 60, # Time to delay batching hook events for target URL(seconds)
      ...
  }

In time mode the deliverer will trigger a delayed batching of hooks. It will
read the time to delay from the :code:`time` setting. This delayed batching
is triggered when the first hook for a target URL is sent to the deliverer.

mixed
``````
.. code-block:: python
  
  HOOK_DELIVERER_SETTINGS = {
      ...
      'time': 60,
      'size': 5,
      ...
  }

The time and size modes can be mixed. The deliverer will batch by whichever
event occurs first. To use this mode, provide both the time and size settings.
The order of the settings in the configuration dictionary does not matter.


Note: It is important to use caution when choosing the configuration values
for the deliverer as this can lead to resource misuse when not done properly.

If this deliverer is selected, do not forget to start a celery worker and a redis
instance for your project.

.. code-block:: bash
  
  celery -A proj worker -l info

.. code-block:: bash

  redis-server

where proj is the name of your project.

Check the `Celery <http://www.celeryproject.org>`_ website for a detailed
example.

retry
``````
.. code-block:: python
  
  HOOK_DELIVERER_SETTINGS = {
      ...
      'retry': {
          'retries': 2, # Number of times to retry failed deliveries
          'retry_interval': 5, # Time to delay between retries(seconds)
      }
      ...
  }

This deliverer can also retry failed deliveries. When the :code:`retry` setting
is provided the deliverer will retry failed deliveries every
:code:`retry_interval` seconds until either successful or :code:`retries`
retries have failed, at which point it will give up. When the deliverer gives
up it will discard all failed hooks for the current target URL. If this setting
is not provided the deliverer will discard failed deliveries.

Example
________

.. code-block:: python

    ### settings.py

    ...

    INSTALLED_APPS = [
    ...
    'rest_hooks_delivery',
    'django.contrib.admin',
    ]

    HOOK_DELIVERER = 'rest_hooks_delivery.deliverers.batch'

    HOOK_DELIVERER_SETTINGS = {
        'size': 3,
        'time': 60,
        # You can comment out the mode you do not need above
        'retry': {
            'retries': 2,
            'retry_interval': 5,
        }
    }
