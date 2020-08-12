from django.conf import settings
from django.contrib import admin, messages
from django.db.models import F
from django.utils.translation import ugettext_lazy as _
from rest_hooks.utils import get_module

from rest_hooks_delivery.models import FailedHook


class UserFilter(admin.SimpleListFilter):
    title = _('user')
    parameter_name = 'user'

    def lookups(self, request, model_admin):
        if not request.user.is_superuser:
            return [(request.user.id, request.user.username),]

        user_ids = FailedHook.objects.all().values_list('user').distinct()
        AuthUserModel = FailedHook._meta.get_field('user').remote_field.model
        users = AuthUserModel.objects.filter(id__in=user_ids).order_by('-is_active', 'username')

        return [(user.id, user.username if user.is_active else "%s (Inactive)" % user.username) for user in users]

    def queryset(self, request, queryset):
        if not request.user.is_superuser:
            return queryset.filter(user=request.user)
        if self.value():
            return queryset.filter(user=self.value())
        return queryset


def retry_hook(modeladmin, request, queryset):
    deliverer = getattr(settings, 'HOOK_DELIVERER', None)
    if not deliverer:
        modeladmin.message_user(request, "No custom HOOK_DELIVERER set in "
                                "settings.py", messages.ERROR)
        return

    deliverer = get_module(deliverer)
    count = 0

    # Ensure that only "valid" requests are run; TODO: does this really matter?
    for hook in queryset.filter(target=F('hook__target'),
                                #event=F('hook__event'), # TODO: this won't match for any.any or model.any events
                                user_id=(
                                    # For non-superusers, limit access to user's own failed webhooks
                                    F('hook__user_id') if request.user.is_superuser else request.user.id)
                                ):
        deliverer(hook.target, hook.payload, hook=hook.hook,
                  failed_hook=hook)
        count += 1
    modeladmin.message_user(request, "Retried %d failed webhooks" % count)
retry_hook.short_description = "Retry selected failed hooks"


class FailedHookAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'event', 'user', 'last_status',
                    'last_retry', 'retries', 'valid', 'hook')
    list_filter = (UserFilter, 'event')
    readonly_fields = ('target', 'event', 'user', 'last_status', 'last_retry',
                       'retries', 'payload', 'response_headers',
                       'response_body')

    #actions = ['delete_selected', retry_hook]
    # ERRORS:
    # <class 'rest_hooks_delivery.admin.FailedHookAdmin'>: (admin.E130) __name__ attributes of actions defined in <class 'rest_hooks_delivery.admin.FailedHookAdmin'> must be unique.
    actions = [retry_hook] # https://docs.djangoproject.com/en/2.2/releases/2.2/#admin-actions-are-no-longer-collected-from-base-modeladmin-classes

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        if not request.user.has_perm('rest_hooks_delivery.change_failedhook'):
            return False
        if obj and obj.user != request.user and not request.user.is_superuser:
            return False
        return True

    def delete_selected(self, request, queryset):
        if not request.user.is_superuser:
            queryset = queryset.filter(user=request.user)

        return admin.actions.delete_selected(self, request, queryset)
    delete_selected.short_description = "Delete selected failed hooks"

    def valid(self, obj):
        if not obj.user.pk == obj.hook.user.pk:
            return False
        
        valid = obj.target == obj.hook.target and obj.event == obj.hook.event
        
        if not valid:
            # check any.any pattern
            hook_event = obj.hook.event
            valid = hook_event == 'any.any'
            
            if not valid:
                # check for module.any pattern
                hook_event = hook_event.split('.')
                valid = hook_event[1] == 'any' and hook_event[0] == obj.event.split('.')[0]
        
        return valid
    valid.boolean = True


admin.site.register(FailedHook, FailedHookAdmin)
