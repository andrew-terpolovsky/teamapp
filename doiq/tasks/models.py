from __future__ import unicode_literals
import json
import redis
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch.dispatcher import receiver
from django.template import Context, Template
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from doiq.chat.models import Chat
from doiq.chat.serializers import ChatSerializer
from doiq.filemanager.models import FileManager


class Task(TimeStampedModel):
    PRIORITIES = (
        (0, _('Low')),
        (1, _('Normal')),
        (2, _('Medium')),
        (3, _('High')),
    )
    STATUSES = (
        (0, _('Not started')),
        (1, _('In-progress')),
        (2, _('Stopped')),
        (3, _('Completed')),
    )

    name = models.CharField(max_length=255, verbose_name=_('name'))
    due_date = models.DateField(verbose_name=_('due date'))
    comment = models.TextField(verbose_name=_('comment'), blank=True, null=True)
    priority = models.IntegerField(choices=PRIORITIES, default=1, verbose_name=_('priority'))
    status = models.IntegerField(choices=STATUSES, default=0, verbose_name=_('status'))
    owner = models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='tasks', verbose_name=_('author'))
    assignee = models.ForeignKey(to=settings.AUTH_USER_MODEL, blank=True, null=True, verbose_name=_('assignee'))
    files = models.ManyToManyField(to=FileManager, blank=True, verbose_name=_('attachments'))
    followers = models.ManyToManyField(
        to=settings.AUTH_USER_MODEL,
        blank=True, related_name='task_following',
        verbose_name=_('followers')
    )
    deleted = models.BooleanField(default=False)
    related_channel = models.ForeignKey(
        to='channel.Channel',
        blank=True, null=True,
        verbose_name=_('Channel'),
        related_name='channel_tasks'
    )

    def __unicode__(self):
        return self.name

    @property
    def activity_count(self):
        return self.activity.count()

    @property
    def done(self):
        return self.status == 3

    @property
    def related_channel_name(self):
        return self.related_channel.name if self.related_channel else ''

    @property
    def expired(self):
        return self.due_date <= timezone.now().date()

    class Meta:
        ordering = ('status', '-id')


class BaseTemplate(models.Model):
    MODULES = (
        (0, 'Tasks'),
        (1, 'Channels'),
    )

    module = models.IntegerField(choices=MODULES, default=0)
    id = models.CharField(max_length=64, verbose_name=_('system name'), primary_key=True)
    html = models.TextField(verbose_name=_('template'))

    class Meta:
        verbose_name = _('template')
        verbose_name_plural = _('templates')


class Activity(TimeStampedModel):
    comment = models.TextField()
    template = models.ForeignKey(to='tasks.BaseTemplate', blank=True, null=True)
    task = models.ForeignKey(to='tasks.Task', related_name='activity')
    sender = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        related_name='activity',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    content_type = models.ForeignKey(
        to=ContentType,
        related_name='notify_target',
        blank=True, null=True,
        on_delete=models.SET_NULL
    )
    object_id = models.CharField(max_length=256, blank=True)
    target = GenericForeignKey('content_type', 'object_id')
    system = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)


@receiver(pre_save, sender=Activity)
def generate_comment(instance, **kwargs):
    if instance.system and not instance.pk:
        context = Context({
            'user': instance.sender,
            'target': instance.target,
            'task': instance.task,
        })
        t = Template(instance.template.html)
        instance.comment = t.render(context)

        # Channel posting
        # TODO: turn off task updates in channel.
        # if instance.task.related_channel:
        #     try:
        #         html = BaseTemplate.objects.get(pk='channel_{0}'.format(instance.template_id)).html
        #         t = Template(html)
        #         channel_msg = t.render(context)
        #     except BaseTemplate.DoesNotExist:
        #         channel_msg = instance.comment
        #     client = redis.StrictRedis(db=8)
        #     notification = Chat.objects.create(channel=instance.task.related_channel, type=3, message=channel_msg, sender=instance.sender)
        #     message_structure = {
        #         'type': 'channel_tasks_modified',
        #         'channel_uid': notification.channel.channel_uid,
        #         'notification': ChatSerializer(notification).data
        #     }
        #     client.publish('channels_todo', json.dumps(message_structure))
        #     del client
