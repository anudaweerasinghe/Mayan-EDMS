from __future__ import unicode_literals

import uuid

from pytz import common_timezones

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.encoding import force_text, python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from mayan.apps.storage.classes import DefinedStorageLazy

from .literals import STORAGE_NAME_COMMON_SHARED_UPLOADED_FILE
from .managers import ErrorLogEntryManager, UserLocaleProfileManager


def upload_to(instance, filename):
    return 'shared-file-{}'.format(uuid.uuid4().hex)


class ErrorLogEntry(models.Model):
    """
    Class to store an error log for any object. Uses generic foreign keys to
    reference the parent object.
    """
    namespace = models.CharField(
        max_length=128, verbose_name=_('Namespace')
    )
    content_type = models.ForeignKey(
        blank=True, on_delete=models.CASCADE, null=True,
        related_name='error_log_content_type', to=ContentType,
    )
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey(
        ct_field='content_type', fk_field='object_id',
    )
    datetime = models.DateTimeField(
        auto_now_add=True, db_index=True, verbose_name=_('Date time')
    )
    result = models.TextField(blank=True, null=True, verbose_name=_('Result'))

    objects = ErrorLogEntryManager()

    class Meta:
        ordering = ('datetime',)
        verbose_name = _('Error log entry')
        verbose_name_plural = _('Error log entries')


@python_2_unicode_compatible
class SharedUploadedFile(models.Model):
    """
    Keep a database link to a stored file. Used to share files between code
    that runs out of process.
    """
    file = models.FileField(
        storage=DefinedStorageLazy(
            name=STORAGE_NAME_COMMON_SHARED_UPLOADED_FILE
        ), upload_to=upload_to, verbose_name=_('File')
    )
    filename = models.CharField(max_length=255, verbose_name=_('Filename'))
    datetime = models.DateTimeField(
        auto_now_add=True, verbose_name=_('Date time')
    )

    class Meta:
        verbose_name = _('Shared uploaded file')
        verbose_name_plural = _('Shared uploaded files')

    def __str__(self):
        return self.filename

    def save(self, *args, **kwargs):
        self.filename = force_text(self.file)
        super(SharedUploadedFile, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.file.storage.delete(self.file.name)
        return super(SharedUploadedFile, self).delete(*args, **kwargs)

    def open(self):
        return self.file.storage.open(self.file.name)


@python_2_unicode_compatible
class UserLocaleProfile(models.Model):
    """
    Stores the locale preferences of a user. Stores timezone and language
    at the moment.
    """
    user = models.OneToOneField(
        on_delete=models.CASCADE, related_name='locale_profile',
        to=settings.AUTH_USER_MODEL, verbose_name=_('User')
    )
    timezone = models.CharField(
        choices=zip(common_timezones, common_timezones), max_length=48,
        verbose_name=_('Timezone')
    )
    language = models.CharField(
        choices=settings.LANGUAGES, max_length=8, verbose_name=_('Language')
    )

    objects = UserLocaleProfileManager()

    class Meta:
        verbose_name = _('User locale profile')
        verbose_name_plural = _('User locale profiles')

    def __str__(self):
        return force_text(self.user)

    def natural_key(self):
        return self.user.natural_key()
    natural_key.dependencies = [settings.AUTH_USER_MODEL]
