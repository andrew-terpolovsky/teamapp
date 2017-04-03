from doiq.accounts.user.serializers import InlineAccountSerializer
from rest_framework import serializers
from .models import Invite


class InviteSerializer(serializers.ModelSerializer):
    emails = serializers.CharField(write_only=True, required=True)
    email = serializers.CharField()
    user = InlineAccountSerializer(read_only=True)
    accepted = serializers.SerializerMethodField(source='get_accepted')

    def get_accepted(self, invitation):
        print self.context['request'].user, invitation
        if invitation.user:
            return bool(self.context['request'].user.friends.filter(id=invitation.user.id).count())
        return False

    class Meta:
        model = Invite
        fields = ('accepted', 'channel', 'created', 'emails', 'email', 'id', 'invited_by', 'modified', 'user')
