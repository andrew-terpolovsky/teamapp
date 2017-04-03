from rest_framework import serializers

from .models import Channel, ChannelMembership
from doiq.accounts.serializers import InlineAccountSerializer


class ReadChannelSerializer(serializers.ModelSerializer):
    owner = InlineAccountSerializer(many=False)
    members = InlineAccountSerializer(many=True)
    tasks_amount = serializers.ReadOnlyField()

    class Meta:
        model = Channel


class CreateChannelSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        instance = super(CreateChannelSerializer, self).create(validated_data)
        ChannelMembership.objects.create(channel=instance, member=instance.owner)
        return instance

    def validate_name(self, value):
        name = self.initial_data.get('name') or ''
        if not name.startswith('#'):
            name = u'#{0}'.format(name)
        if Channel.objects.filter(owner_id=self.initial_data.get('owner'), name=name).count():
            raise serializers.ValidationError(u'Name should be unique. You have already channel ' + name)
        return value

    class Meta:
        model = Channel
