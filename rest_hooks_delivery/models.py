from django.conf import settings
from django.db import models

HOOK_EVENTS = getattr(settings, 'HOOK_EVENTS', None)
if HOOK_EVENTS is None:
    raise Exception('You need to define settings.HOOK_EVENTS!')
AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class FailedHook(models.Model):
    last_retry = models.DateTimeField(auto_now=True, editable=False,
                                      db_index=True)
    target = models.URLField('original target URL', max_length=255,
                             editable=False, db_index=True)
    event = models.CharField(max_length=64, db_index=True,
                             choices=[(e, e) for e in
                                      sorted(HOOK_EVENTS.keys())],
                             editable=False)
    user = models.ForeignKey(AUTH_USER_MODEL, editable=False, on_delete=models.PROTECT)
    payload = models.TextField(editable=False)
    response_headers = models.TextField(editable=False, max_length=65535)
    response_body = models.TextField(editable=False, max_length=65535)
    last_status = models.PositiveSmallIntegerField(editable=False,
                                                   db_index=True)
    retries = models.PositiveIntegerField(editable=False, db_index=True,
                                          default=1)

    hook = models.ForeignKey('rest_hooks.Hook', editable=False, on_delete=models.PROTECT)

    def __unicode__(self):
        return '%s [%d]' % (self.target, self.last_status)

    class Meta:
        ordering = ('-last_retry',)
