import json

from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import now
from rest_hooks.utils import get_module

from rest_hooks_delivery.models import FailedHook


class Command(BaseCommand):
    
    def handle(self, *args, **options):
        deliverer = getattr(settings, 'HOOK_DELIVERER', None)
        if not deliverer:
            raise CommandError('No custom HOOK_DELIVERER set in settings.py')
            return 5
        deliverer = get_module(deliverer)
        
        count = 0

        # Backoff schedule: 1min, 3min, 10min, 30min, 60min
        backoff_minutes = {
            1: 1,
            2: 2,
            3: 7,
            4: 20,
            5: 30,
        }
        
        for hook in FailedHook.objects.filter(retries__lte=5): # TODO: Add backoff algorithm

            if hook.last_retry + timedelta(minutes=backoff_minutes.get(hook.retries, 120)) > now():
                continue # It's not time yet to retry
            
            event_model = hook.event.split('.')[0] + '.'

            payload_dict = json.loads(hook.payload)
            has_older_hooks = len(FailedHook.objects.filter(
                event__startswith=event_model,
                payload__contains=payload_dict['url'], 
                pk__lt=hook.pk)) > 0
            
            if has_older_hooks:
                # Don't retry newer hooks if an older one fails for a model url
                print('Skipping failed hook because there is an older one that '
                    'needs to succeed first')
                continue

            #TODO: Handle parents and foreign key hooks first

            deliverer(hook.target, hook.payload, hook=hook.hook, failed_hook=hook)
            count += 1
        
        self.stdout.write('Retried {} failed webhooks'.format(count))
