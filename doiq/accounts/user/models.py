from __future__ import unicode_literals

import doiq.accounts
import redis
import json
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core import validators
from django.db import models
from django.db.models import Q
from django.dispatch import receiver
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from doiq.accounts.user.manager import UserManager
from doiq.channel.models import ChannelMembership
from sorl.thumbnail import get_thumbnail
from django.core.cache import cache
from hashlib import md5
from doiq.accounts.user.signals import user_profile_was_changed


@python_2_unicode_compatible
class User(AbstractBaseUser, PermissionsMixin):
    STATUSES = (
        (0, _('Offline')),
        (1, _('Online')),
    )
    email = models.EmailField(
        _('email address'),
        max_length=255,
        unique=True,
        error_messages={
            'unique': _("A user with that email already exists."),
        },
    )
    full_name = models.CharField(_('full name'), max_length=30, blank=True)
    username = models.CharField(
        verbose_name=_('username'),
        max_length=70,
        unique=True,
        help_text=_('Required. 70 characters or fewer. Letters, digits only.'),
        validators=[
            validators.RegexValidator(
                r'^[\w]+$',
                _('Enter a valid username. This value may contain only letters and numbers.')
            ),
        ],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    is_staff = models.BooleanField(
        verbose_name=_('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into admin site.'),
    )
    is_active = models.BooleanField(
        verbose_name=_('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    subscribed = models.BooleanField(default=True)
    image = models.ForeignKey(
        to='filemanager.FileManager',
        verbose_name=_('User picture'),
        blank=True, null=True,
        related_name='avatars', on_delete=models.SET_NULL
    )
    status = models.IntegerField(choices=STATUSES, default=1)
    timezone = models.CharField(
        verbose_name=_('time zone'),
        max_length=64,
        default=settings.TIME_ZONE
    )
    friends = models.ManyToManyField('self', blank=True, symmetrical=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username',)

    def __str__(self):
        return self.email

    def crop_small_picture(self, raw_data=None):
        cache_key = md5('{0}-image-small'.format(self.id)).hexdigest()
        cache_thumb = cache.get(cache_key)
        if cache_thumb:
            return cache_thumb
        if not raw_data:
            img = get_thumbnail(self.image.file.url, '52x52', crop='center')
        else:
            img = get_thumbnail(raw_data.file, '52x52', crop='center')
        cache.set(cache_key, img.url, 15 * 60)
        return img.url

    def crop_medium_picture(self, raw_data=None):
        cache_key = md5('{0}-image-medium'.format(self.id)).hexdigest()
        cache_thumb = cache.get(cache_key)
        if cache_thumb:
            return cache_thumb
        if not raw_data:
            img = get_thumbnail(self.image.file.url, '105x105', crop='center')
        else:
            img = get_thumbnail(raw_data.file, '105x105', crop='center')
        cache.set(cache_key, img.url, 15 * 60)
        return img.url

    @property
    def get_picture(self):
        if self.image:
            return self.crop_small_picture()
        return None

    @property
    def get_picture_medium(self):
        if self.image:
            return self.crop_medium_picture()
        return None

    def get_short_name(self):
        """
        :return: The short name for the user.
        """
        return self.full_name

    def get_full_name(self):
        """
        :return: The first_name plus the last_name, with a space in between.
        """
        return self.full_name or self.username or self.email

    def get_channels(self):
        if self.channels.count():
            return map(
                lambda x: {'name': x.name, 'id': x.id, 'channel_uid': x.channel_uid, 'opened': x.opened,
                           'counter_unread': x.channelmembership_set.filter(member=self)[0].counter_unread,
                           'type': x.type},
                self.channels.extra(select={'is_owner': 'SELECT owner_id = %s', 'lower_name': 'lower(name)'}, select_params=(self.id, ))
                    .order_by('-opened', 'lower_name', 'id')
            )
        return []

    def get_all_available_private_channals(self):
        # friends = self.friends.values_list('id', flat=True)
        private_channals_membership = ChannelMembership.objects.filter(channel__type=1,
                                                                       member=self)  # .values_list('channel', flat=True)
        return private_channals_membership


@receiver(models.signals.m2m_changed, sender=User.friends.through)
def clear_accepted_invites_on_friend_delete(sender, instance, action, pk_set, *args, **kwargs):
    if action == 'post_remove':
        doiq.accounts.invites.models.Invite.objects.filter(
            Q(accepted=True) & Q(
                Q(invited_by=instance, user_id__in=pk_set) | Q(user_id=instance, invited_by_id__in=pk_set)
            )
        ).delete()

@receiver(user_profile_was_changed, sender=User)
def handle_profile_changed_socket_notify(sender, user, **kwargs):
    picture_small = kwargs.get('picture_small')
    full_name = kwargs.get('full_name')
    client = redis.StrictRedis(db=8)
    message_struct = {
        'type': 'profile_changed',
        'avatar': picture_small,
        'full_name': full_name,
        'user_id': user.id
    }
    client.publish('user_todo', json.dumps(message_struct))
    del client