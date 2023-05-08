from django.conf import settings
from django.db import models
from django.utils import timezone


class SystemField(models.Model):

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Created by',
        blank=True, null=True,
        related_name='%(app_label)s_%(class)s_created',
        on_delete=models.SET_NULL
    )
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Modified by',
        blank=True, null=True,
        related_name='%(app_label)s_%(class)s_modified',
        on_delete=models.SET_NULL
    )
    is_migrated = models.BooleanField(editable=False, null=True)

    # class Meta:
    #     abstract = True
    #     app_label = 'systemfield'

    def save(self, *args, **kwargs) -> None:
        update_fields = kwargs.get('update_fields')
        if update_fields is not None:
            # update_fields can be any iterable
            update_fields = list(update_fields)

        if update_fields:
            if 'modified_by' not in update_fields:
                update_fields.append('modified_by')
            if 'modified_at' not in update_fields:
                update_fields.append('modified_at')

        kwargs['update_fields'] = update_fields

        return super().save(*args, **kwargs)
