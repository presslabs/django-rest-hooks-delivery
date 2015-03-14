# -*- coding: utf-8 -*-
# vim: ft=python:sw=4:ts=4:sts=4:et:
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import F
from rest_hooks.utils import get_module

from rest_hooks_delivery.models import FailedHook


class Command(BaseCommand):
    def handle(self, *args, **options):
        deliverer = getattr(settings, 'HOOK_DELIVERER', None)
        if not deliverer:
            raise CommandError("No custom HOOK_DELIVERER set in settings.py")
            return 5
        deliverer = get_module(deliverer)
        count = 0
        for hook in FailedHook.objects.filter(target=F('hook__target'),
                                              event=F('hook__event'),
                                              user_id=F('hook__user_id')):
            deliverer(hook.target, hook.payload, hook=hook.hook,
                      cleanup=True)
            count += 1
        self.stdout.write("Retried %d failed webhooks" % count)
