from __future__ import unicode_literals
import uuid
import redis
import json
import doiq.chat
from django.apps import apps
from django.conf import settings
from django.db import models
from django.db.models import signals, Q
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django_extensions.db.models import TimeStampedModel
from django.dispatch.dispatcher import receiver
from .signals import channel_ownership_changed, friend_added_to_channel, force_update_channel, \
    kicked_member_from_channel, file_binded_state_in_channel
import doiq.channel

User = settings.AUTH_USER_MODEL


def get_channel_uid():
    return str(uuid.uuid4())


class Channel(TimeStampedModel):
    owner = models.ForeignKey(User)
    name = models.CharField(_('Channel Name'), max_length=255)
    members = models.ManyToManyField(
        User, related_name="channels", blank=True,
        through='ChannelMembership'
    )
    channel_uid = models.CharField(
        _('Unique channel identifier'),
        max_length=255,
        unique=True,
        default=get_channel_uid,
        db_index=True
    )
    type = models.PositiveSmallIntegerField(
        _('Type of channel'),
        default=2,
        choices=(
            (1, 'Private-relate'),
            (2, 'Channel-relate'),
        ))
    description = models.CharField(
        _('Description'), max_length=255, null=True, blank=True
    )
    opened = models.BooleanField(_('Opened'), default=True, blank=True)
    members_contacts = models.TextField(blank=True, null=True)

    def tasks_amount(self):
        return self.channel_tasks.filter(~Q(status=3), Q(deleted=False)).count()

    def update_members_contacts(self):
        members = ChannelMembership.objects.filter(channel=self)
        members_contacts = []
        for membership in members.iterator():
            members_contacts.append({
                'id': membership.member.id,
                'username': membership.member.username,
                'email': membership.member.username,
                'full_name': membership.member.full_name
            })
        self.members_contacts = json.dumps(members_contacts)
        self.save()

    def __unicode__(self):
        return self.name


class ChannelMembership(models.Model):
    date_joined = models.DateTimeField(_('Join date'), default=timezone.now)
    member = models.ForeignKey(User)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    counter_unread = models.PositiveIntegerField(
        _('Total unread messages'), default=0
    )
    private_channel_opened = models.BooleanField(default=False)

    def __unicode__(self):
        if self.channel.type == 1:
            return u'P:{channel}'.format(channel=self.channel.name)
        elif self.channel.type == 2:
            return u'C:{channel}-{member}'.format(channel=self.channel.name, member=self.member.username)

    class Meta:
        unique_together = ['member', 'channel']


@receiver(signals.post_save, sender=ChannelMembership)
def handle_new_channel_created(instance, raw, created, using, update_fields, **kwargs):
    if created:
        client = redis.StrictRedis(db=8)
        message_struct = {
            'type': 'update_channel_connected_users',
            'channel_id': instance.channel.id,
            'channel_uid': instance.channel.channel_uid,
            'message': getattr(instance, '_message', None),
            'user': {
                'email': instance.member.email,
                'full_name': instance.member.full_name or instance.member.username,
                'id': instance.member.id,
                'image': instance.member.image.file.url if instance.member.image else None,
                'username': instance.member.username
            }
        }
        client.publish('channels_todo', json.dumps(message_struct))
        del client
    instance.channel.update_members_contacts()


@receiver(force_update_channel, sender=ChannelMembership)
def handle_force_update_channel(channel, user, **kwargs):
    client = redis.StrictRedis(db=8)
    message_struct = {
        'type': 'update_channel_connected_users',
        'channel_id': channel.id,
        'user': {
                'email': user.email,
                'full_name': user.full_name or user.username,
                'id': user.id,
                'image': user.image.file.url if user.image else None,
                'username': user.username
            }
    }
    client.publish('channels_todo', json.dumps(message_struct))
    del client


@receiver(kicked_member_from_channel, sender=ChannelMembership)
def handle_kicked_member(membership, owner, **kwargs):
    client = redis.StrictRedis(db=8)
    template = '{user} was kicked from this channel.'.format(user=membership.member.username)
    notification = doiq.chat.models.Chat.objects.create(channel=membership.channel, type=3, message=template, sender=owner)
    message_struct = {
        'type': 'channel_kicked_member',
        'channel_uid': membership.channel.channel_uid,
        'notification': doiq.chat.serializers.ChatSerializer(notification).data
    }
    message_struct['notification']['member_id'] = membership.member.id
    message_struct['notification']['channel_name'] = membership.channel.name
    print message_struct
    client.publish('channels_todo', json.dumps(message_struct))
    del client
    membership.channel.update_members_contacts()


@receiver(signals.pre_save, sender=Channel)
def handle_channel_archived(instance, raw, using, update_fields, **kwargs):
    if instance.pk:
        if not instance.opened and Channel.objects.filter(id=instance.id, opened=True).count():
            client = redis.StrictRedis(db=8)
            message_struct = {
                'type': 'channel_archived',
                'channel': {
                    'channel_uid': instance.channel_uid,
                    'name': instance.name
                }
            }
            client.publish('channels_todo', json.dumps(message_struct))
            del client


@receiver(channel_ownership_changed, sender=Channel)
def handle_owner_had_changed(channel, owner, new_owner, **kwargs):
    client = redis.StrictRedis(db=8)
    print owner, new_owner
    message_struct = {
        'type': 'channel_ownership_changed',
        'channel': doiq.channel.serializers.ReadChannelSerializer(channel).data,
        'user_id': new_owner.id
    }
    client.publish('channels_todo', json.dumps(message_struct))
    del client


@receiver(friend_added_to_channel, sender=Channel)
def handle_friend_added_to_channel(channel, friend, inviter, **kwargs):
    client = redis.StrictRedis(db=8)
    message_struct = {
        'type': 'friend_added_to_channel',
        'channel': doiq.channel.serializers.ReadChannelSerializer(channel).data,
        'user_id': friend.id
    }
    client.publish('channels_todo', json.dumps(message_struct))
    del client

@receiver(file_binded_state_in_channel)
def handle_file_binded_state_in_channel(channel_uid, file_id, deleted, **kwargs):
    print 'kazaaaaaaaa'
    client = redis.StrictRedis(db=8)
    message_struct = {
        'type': 'file_binded_state_in_channel',
        'channel': channel_uid,
        'deleted': deleted,
        'file_id': file_id
    }
    client.publish('channels_todo', json.dumps(message_struct))
    del client
