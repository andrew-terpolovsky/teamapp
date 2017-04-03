from hashlib import md5

import django.contrib.auth.password_validation as validators
from django.conf import settings
from django.core import exceptions
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.db import connection
from django.db.models import Q
from django.template.loader import render_to_string
from passwords import validators as password_validators
from rest_framework import serializers

from doiq.accounts import constants
from doiq.accounts.user.signals import user_profile_was_changed
from .models import User


class InlineAccountSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField(source='get_full_name')
    image = serializers.ReadOnlyField(source='get_picture')

    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'username', 'image')


class FriendsAccountSerializer(InlineAccountSerializer):
    """
    With personal channel uid.
    """
    private_channel_uid = serializers.SerializerMethodField(source='get_private_channel_uid')
    private_channel_opened = serializers.SerializerMethodField(source='get_private_channel_opened')
    counter_unread = serializers.SerializerMethodField(source='get_counter_unread')

    def get_private_channel_uid(self, obj):
        cursor = connection.cursor()
        cursor.execute('SELECT c.channel_uid FROM channel_channel c '
                       'JOIN channel_channelmembership cm1 ON c.id = cm1.channel_id AND cm1.member_id = %s '
                       'JOIN channel_channelmembership cm2 ON c.id = cm2.channel_id AND cm2.member_id = %s '
                       'WHERE c.type = 1',
                       (self.context['request'].user.id, obj.id)
                       )
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None

    def get_counter_unread(self, obj):
        cursor = connection.cursor()
        cursor.execute('SELECT cm1.counter_unread FROM channel_channel c '
                       'JOIN channel_channelmembership cm1 ON c.id = cm1.channel_id AND cm1.member_id = %s '
                       'JOIN channel_channelmembership cm2 ON c.id = cm2.channel_id AND cm2.member_id = %s '
                       'WHERE c.type = 1',
                       (self.context['request'].user.id, obj.id)
                       )
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return 0

    def get_private_channel_opened(self, obj):
        cursor = connection.cursor()
        cursor.execute('SELECT cm1.private_channel_opened FROM channel_channel c '
                       'JOIN channel_channelmembership cm1 ON c.id = cm1.channel_id AND cm1.member_id = %s '
                       'JOIN channel_channelmembership cm2 ON c.id = cm2.channel_id AND cm2.member_id = %s '
                       'WHERE c.type = 1',
                       (self.context['request'].user.id, obj.id)
                       )
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return False

    class Meta:
        model = User
        fields = (
            'private_channel_uid', 'private_channel_opened', 'counter_unread', 'id', 'email', 'full_name', 'username',
            'image')


class PrivateChatsAccountSerializer(serializers.Serializer):
    private_channel_uid = serializers.SerializerMethodField(source='get_private_channel_uid')
    private_channel_opened = serializers.SerializerMethodField(source='get_private_channel_opened')
    counter_unread = serializers.SerializerMethodField(source='get_counter_unread')
    id = serializers.SerializerMethodField(source='get_id')
    username = serializers.SerializerMethodField(source='get_username')
    full_name = serializers.SerializerMethodField(source='get_full_name')

    def get_private_channel_uid(self, obj):
        return obj.channel.channel_uid

    def get_counter_unread(self, obj):
        return obj.counter_unread

    def get_private_channel_opened(self, obj):
        return obj.private_channel_opened

    def get_id(self, obj):
        return obj.__class__.objects.filter(channel=obj.channel).filter(~Q(id=obj.id))[0].member.id

    def get_username(self, obj):
        return obj.__class__.objects.filter(channel=obj.channel).filter(~Q(id=obj.id))[0].member.username

    def get_full_name(self, obj):
        return obj.__class__.objects.filter(channel=obj.channel).filter(~Q(id=obj.id))[0].member.full_name


class AccountSerializer(serializers.ModelSerializer):
    _password_style = {'input_type': 'password'}
    old_password = serializers.CharField(allow_blank=True, required=False, write_only=True, style=_password_style)
    new_password = serializers.CharField(allow_blank=True, required=False, write_only=True, style=_password_style)
    confirm_password = serializers.CharField(allow_blank=True, required=False, write_only=True, style=_password_style)
    friends = FriendsAccountSerializer(many=True, read_only=True)
    private_chats = PrivateChatsAccountSerializer(many=True, read_only=True,
                                                  source='get_all_available_private_channals')
    channels = serializers.ReadOnlyField(source='get_channels')
    get_picture = serializers.CharField(read_only=True)
    get_picture_medium = serializers.CharField(read_only=True)
    get_full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        read_only_fields = ('id', 'email', 'username', 'is_active', 'status', 'password')

    def validate(self, data):
        data = super(AccountSerializer, self).validate(data)
        user = self.context['request'].user
        old_pwd = data.get('old_password')
        new_pwd = data.get('new_password')
        confirm_pwd = data.get('confirm_password')

        if new_pwd:
            try:
                validators.validate_password(password=new_pwd)
                password_validators.complexity(new_pwd)
                password_validators.common_sequences(new_pwd)
                password_validators.validate_length(new_pwd)
            except exceptions.ValidationError as e:
                raise serializers.ValidationError({'new_password': [e.messages]})
            if new_pwd != confirm_pwd:
                raise serializers.ValidationError({'new_password': [constants.PASSWORD_MISMATCH_ERROR]})
            if not user.check_password(old_pwd):
                raise serializers.ValidationError({'old_password': [constants.INVALID_PASSWORD_ERROR]})

        return data

    def update(self, instance, validated_data):
        if instance.image != validated_data.get('image', instance.image):
            cache_key_small = md5('{0}-image-small'.format(instance.id)).hexdigest()
            cache_key_medium = md5('{0}-image-medium'.format(instance.id)).hexdigest()
            cache.delete_many([cache_key_small, cache_key_medium])
            if validated_data.get('image'):
                picture_small = instance.crop_small_picture(validated_data.get('image'))
                instance.crop_medium_picture(validated_data.get('image'))
                user_profile_was_changed.send(sender=User, user=instance, picture_small=picture_small)
        print instance.full_name, validated_data.get('full_name', instance.full_name)
        if instance.full_name != validated_data.get('full_name', instance.full_name):
            if validated_data.get('full_name'):
                user_profile_was_changed.send(sender=User, user=instance, full_name=validated_data.get('full_name'))
        instance.full_name = validated_data.get('full_name', instance.full_name)
        instance.image = validated_data.get('image', instance.image)
        instance.timezone = validated_data.get('timezone', instance.timezone)
        password = validated_data.get('new_password')
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class FriendsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'get_full_name', 'username', 'get_picture')


class RegistrationSerializer(serializers.HyperlinkedModelSerializer):
    def validate_password(self, password):
        password_validators.complexity(password)
        password_validators.common_sequences(password)
        password_validators.validate_length(password)
        return password

    class Meta:
        model = User
        fields = ('email', 'username', 'password')


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, data):
        users = User.objects.filter(email=data)
        if not users.count():
            raise serializers.ValidationError({'email': [constants.EMAIL_NOT_FOUND]})
        return users[0]

    def create(self, validated_data):
        user = validated_data['email']
        # token = urlsafe_base64_encode('{0}:do-iq-app:{1}'.format(user.email, user.pk))
        password = User.objects.make_random_password()
        user.set_password(password)
        user.save()
        context = dict(
            domain=settings.HOSTNAME,
            user=user,
            password=password,
        )
        msg = EmailMultiAlternatives(
            subject=render_to_string('emails/accounts/reset_password_subject.txt', context),
            body=render_to_string('emails/accounts/reset_password.txt', context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
            reply_to=[settings.DEFAULT_FROM_EMAIL]
        )
        msg.attach_alternative(render_to_string('emails/accounts/reset_password.html', context), "text/html")
        validated_data['sent'] = msg.send()
        return validated_data
