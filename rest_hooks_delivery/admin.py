# -*- coding: utf-8 -*-
# vim: ft=python:sw=4:ts=4:sts=4:et:
from django.conf import settings
from django.contrib import admin, messages
from django.db.models import F
from rest_hooks.utils import get_module

from rest_hooks_delivery.models import FailedHook


def retry_hook(modeladmin, request, queryset):
    deliverer = getattr(settings, 'HOOK_DELIVERER', None)
    if not deliverer:
        modeladmin.message_user(request, "No custom HOOK_DELIVERER set in "
                                "settings.py", messages.ERROR)
        return

    deliverer = get_module(deliverer)
    count = 0
    for hook in queryset.filter(target=F('hook__target'),
                                event=F('hook__event'),
                                user_id=F('hook__user_id')):
        deliverer(hook.target, hook.payload, hook=hook.hook,
                  cleanup=True)
        count += 1
    modeladmin.message_user(request, "Retried %d failed webhooks" % count)
retry_hook.short_description = "Retry selected hooks"


class FailedHookAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'event', 'user', 'last_status',
                    'last_retry', 'retries', 'valid', 'hook')
    readonly_fields = ('target', 'event', 'user', 'last_status', 'last_retry',
                       'retries', 'payload', 'response_headers',
                       'response_body')

    actions = (retry_hook, )

    def has_add_permission(self, request):
        return False

    def valid(self, obj):
        return (obj.target == obj.hook.target and obj.event == obj.hook.event
                and obj.user.pk == obj.hook.user.pk)
    valid.boolean = True


admin.site.register(FailedHook, FailedHookAdmin)
