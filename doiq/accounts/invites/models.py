from __future__ import unicode_literals

import redis
import json

from django.conf import settings
from django.core import signing
from django.core.urlresolvers import reverse
from django.db import connection
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from doiq.channel.models import Channel, ChannelMembership
import doiq.accounts
from doiq.utils.mail import send_email


class Invite(TimeStampedModel):
    invited_by = models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='invitees')
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, blank=True, related_name='invite')
    channel = models.ForeignKey(Channel, null=True, blank=True, related_name='invites')
    email = models.EmailField(
        _('email address'),
        max_length=255,
        error_messages={
            'unique': _("This email has already been invited."),
        },
    )
    accepted = models.BooleanField(_('Accepted'), default=False, blank=True)

    def __unicode__(self):
        return u'{} invited by {}'.format(self.email, self.invited_by)

    def get_signature(self):
        signature_body = {
            'pk': self.pk,
            'email': self.email
        }
        if self.channel:
            signature_body.update({'channel': self.channel.channel_uid})
        return signing.dumps(signature_body)

    def get_invite_link(self):
        return reverse(
            'accounts:accept_invite',
            kwargs={'signature': self.get_signature()}
        )

    def send_invite_email(self, request=None):
        return send_email(
            subject='Join Invitation',
            email=self.email,
            template='emails/accounts/invite.html',
            context={'invite': self},
            tags=['invite'],
            request=request
        )

    @staticmethod
    def send_notification_invited_to_channel_email(invitee, channel, inviter):
        return send_email(
            subject='You have been added to channel',
            email=invitee.email,
            template='emails/accounts/invited_to_channel.html',
            context={'invitee': invitee, 'channel': channel, 'inviter': inviter},
            tags=['invite', 'channel']
        )

    @classmethod
    def verify_signature(cls, signature):
        try:
            return signing.loads(signature)
        except Exception:
            return {}

    class Meta:
        ordering = ('-created',)

class Request_(object):
    pass

@receiver(pre_save, sender=Invite)
def invite_invite_handler(sender, instance, created=False, **kwargs):
    """
        Save invite receiver handler
        Checks if invited user is not in invitees friends list and add it.
    """
    if instance.user and instance.accepted and not created and not Invite.objects.get(pk=instance.pk).accepted:
        invited_by = instance.invited_by
        user = instance.user

        if not invited_by.friends.filter(id=instance.user.id).exists():
            invited_by.friends.add(instance.user)
        # if not user.friends.filter(id=instance.invited_by.id).exists():
        #     user.friends.add(instance.invited_by)
        if instance.channel and not ChannelMembership.objects.filter(member=user, channel=instance.channel).count():
            ChannelMembership.objects.create(member=user, channel=instance.channel)

        client = redis.StrictRedis(db=8)
        request = Request_()
        setattr(request, 'user', invited_by)
        message_struct = {
            'type': 'add_invitee_as_friend_to_inviter',
            'friend': doiq.accounts.serializers.FriendsAccountSerializer(
                user,
                context={'request': request}
            ).data,
            'member': instance.channel.channel_uid if instance.channel else None,
            'user_id': invited_by.id
        }
        client.publish('friendship_todo', json.dumps(message_struct))
        del client
