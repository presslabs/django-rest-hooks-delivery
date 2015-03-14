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

Make sure you have added :code:`rest_hooks_delivery` to the list of
:code:`INSTALLED_APPS` before :code:`django.contrib.admin` and that you have
set :code:`HOOK_DELIVERER` to one of the available deliverers. Currently only
:code:`rest_hooks_delivery.deliverers.retry` is available.

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

