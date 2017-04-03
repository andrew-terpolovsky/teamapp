from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.template import Context


# class BaseTemplate(models.Model):
#     system_name = models.CharField(max_length=64, verbose_name=u'system name')
#     type = models.ForeignKey(to='activity.ActivityType', verbose_name=u'activity type', default=0)
#     html = models.TextField(verbose_name=u'body', blank=True)
#
#     class Meta:
#         abstract = True
#
#
# class Activity(models.Model):
#     template = models.ForeignKey(to='activity.LogTemplate', blank=True, null=True)
#     html = models.TextField(verbose_name='body', blank=True, null=True)
#     recipient = models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='logs', blank=True, null=True)
#     timestamp = models.DateTimeField(auto_now_add=True, editable=False)
#     # target object
#     content_type = models.ForeignKey(to=ContentType, related_name='notify_target', blank=True, null=True)
#     object_id = models.CharField(max_length=256)
#     target = GenericForeignKey('content_type', 'object_id')
#     # action object
#     action_content_type = models.ForeignKey(to=ContentType, related_name='notify_action_object', blank=True, null=True)
#     action_object_id = models.CharField(max_length=256, blank=True)
#     action = GenericForeignKey('action_content_type', 'action_object_id')
#     # flags
#     read = models.BooleanField(default=False)
#     public = models.BooleanField(default=False)
#     deleted = models.BooleanField(default=False)
#
#     def render_email(self, user=False):
#         context = Context({
#             'target': self.target,
#             'action': self.action,
#             'recipient': self.recipient,
#             'domain': settings.DOMAIN_NAME,
#             'user': user
#         })
#         return {
#             'subject': self.template.name.render(context),
#             'html': self.template.html.render(context),
#             'text': self.template.text.render(context)
#         }
#
#     def output(self):
#         return {
#             'id': self.pk,
#             'level': self.template.level,
#             'timestamp': self.timestamp,
#             'html': self.html
#         }
#
#     class Meta:
#         ordering = ['-timestamp']
#         verbose_name = 'notification'
#         verbose_name_plural = 'notifications'
